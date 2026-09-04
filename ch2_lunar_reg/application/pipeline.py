"""
Enterprise Registration Pipeline Facade.
ISRO Chandrayaan-2 Planetary Remote Sensing (SIH PS 26166).

Unifies:
1. Lommel-Seeliger / Hapke Photometric Normalization
2. Scale-Space GSD Resampling & Nyquist Decimation
3. Phase Congruency & RIFT Feature Representation
4. Adaptive Non-Maximal Suppression (ANMS) / Grid Spatial Allocator
5. USAC-MAGSAC++ Robust Model Fitting
6. 2D Quadratic Taylor-Series Sub-Pixel Peak Refinement (RMSE < 0.4 px)
7. Thin-Plate Spline (TPS) & Affine/Homography Warping
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from ch2_lunar_reg.domain.models import (
    GeoRaster,
    KeypointMatch,
    RegistrationMetrics,
    RegistrationResult,
    SensorModality,
    SunAngles,
    TransformationModel,
)
from ch2_lunar_reg.domain.photometric import LunarPhotometricNormalizer
from ch2_lunar_reg.domain.phase_congruency import (
    PhaseCongruencyEngine,
    RIFTDescriptorExtractor,
)
from ch2_lunar_reg.domain.transformation import (
    GeometricTransformationSolver,
    ThinPlateSplineTransformer,
)
from ch2_lunar_reg.application.scale_space import HierarchicalScaleSpaceRegistrar
from ch2_lunar_reg.application.spatial_allocator import (
    AdaptiveNonMaximalSuppression,
    GridSpatialAllocator,
)
from ch2_lunar_reg.application.subpixel_refiner import TaylorSubpixelRefiner
from ch2_lunar_reg.application.robust_matcher import (
    RobustDescriptorMatcher,
    UsacMagsacEstimator,
)


class LunarRegistrationPipeline:
    """
    End-to-end mission pipeline for Chandrayaan-2 optical image correspondence.
    """

    def __init__(
        self,
        target_features: int = 500,
        enable_photometric_norm: bool = True,
        enable_anms: bool = True,
        enable_subpixel: bool = True,
        transformation_model: TransformationModel = TransformationModel.AFFINE,
    ) -> None:
        self.target_features = target_features
        self.enable_photometric = enable_photometric_norm
        self.enable_anms = enable_anms
        self.enable_subpixel = enable_subpixel
        self.transformation_model = transformation_model

        # Subsystems
        self.photometric_normalizer = LunarPhotometricNormalizer()
        self.scale_registrar = HierarchicalScaleSpaceRegistrar()
        self.pc_engine = PhaseCongruencyEngine(num_scales=4, num_orientations=6)
        self.rift_extractor = RIFTDescriptorExtractor(patch_size=40, spatial_bins=4, num_orientations=6)
        self.anms = AdaptiveNonMaximalSuppression(robust_coefficient=0.90)
        self.spatial_allocator = GridSpatialAllocator(grid_rows=10, grid_cols=10)
        self.matcher = RobustDescriptorMatcher(ratio_threshold=0.85, mutual_check=True)
        self.usac_magsac = UsacMagsacEstimator(pixel_threshold=2.0)
        self.subpixel_refiner = TaylorSubpixelRefiner(patch_radius=10)

    def _detect_candidate_keypoints(self, max_moment: np.ndarray, max_pts: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detects prominent physical features on Phase Congruency M_max map.
        Uses Shi-Tomasi / Good Features to Track on the invariant moment surface.
        """
        pts_cv = cv2.goodFeaturesToTrack(
            max_moment.astype(np.float32),
            maxCorners=max_pts * 2,
            qualityLevel=0.01,
            minDistance=3.0,
            blockSize=5,
            useHarrisDetector=False,
        )
        if pts_cv is None or len(pts_cv) == 0:
            return np.empty((0, 2), dtype=np.float32), np.empty(0, dtype=np.float32)

        pts = pts_cv.reshape(-1, 2)
        h, w = max_moment.shape
        # Feature responses from M_max intensity
        responses = np.array([
            max_moment[min(int(round(y)), h - 1), min(int(round(x)), w - 1)]
            for (x, y) in pts
        ], dtype=np.float32)

        return pts, responses

    def register(
        self,
        ref_image: np.ndarray,
        target_image: np.ndarray,
        ref_sun: Optional[SunAngles] = None,
        target_sun: Optional[SunAngles] = None,
        ref_gsd: float = 1.0,
        target_gsd: float = 1.0,
    ) -> RegistrationResult:
        """
        Executes full multi-modal registration pipeline.
        
        Args:
            ref_image: Reference lunar image (e.g. TMC-2 or OHRC base).
            target_image: Target lunar image under varying sun angle/modality.
            ref_sun: Solar geometry for reference image.
            target_sun: Solar geometry for target image.
            ref_gsd: Ground Sampling Distance of reference (m/pixel).
            target_gsd: Ground Sampling Distance of target (m/pixel).
            
        Returns:
            RegistrationResult containing transform, inliers, metrics, and warped image.
        """
        start_time = time.perf_counter()

        # Step 1: Ground Sampling Distance Scale Normalization
        img_ref_scaled, img_tgt_scaled, scale_ratio = self.scale_registrar.resample_to_common_gsd(
            ref_image, ref_gsd, target_image, target_gsd
        )

        # Step 2: Photometric Normalization (Lommel-Seeliger)
        if self.enable_photometric and ref_sun is not None:
            norm_ref, _ = self.photometric_normalizer.normalize_lommel_seeliger(img_ref_scaled, ref_sun)
        else:
            norm_ref = cv2.normalize(img_ref_scaled.astype(np.float32), None, 0.0, 1.0, cv2.NORM_MINMAX)

        if self.enable_photometric and target_sun is not None:
            norm_tgt, _ = self.photometric_normalizer.normalize_lommel_seeliger(img_tgt_scaled, target_sun)
        else:
            norm_tgt = cv2.normalize(img_tgt_scaled.astype(np.float32), None, 0.0, 1.0, cv2.NORM_MINMAX)

        # Step 3: Phase Congruency & RIFT Maximum Index Map (MIM)
        pc_ref = self.pc_engine.compute(norm_ref)
        pc_tgt = self.pc_engine.compute(norm_tgt)

        # Step 4: Candidate Feature Detection on Invariant Moment Maps
        kps_ref_raw, resp_ref_raw = self._detect_candidate_keypoints(pc_ref.max_moment, self.target_features * 2)
        kps_tgt_raw, resp_tgt_raw = self._detect_candidate_keypoints(pc_tgt.max_moment, self.target_features * 2)

        if len(kps_ref_raw) < 4 or len(kps_tgt_raw) < 4:
            empty_metrics = RegistrationMetrics(
                num_detected_ref=len(kps_ref_raw),
                num_detected_target=len(kps_tgt_raw),
                num_initial_matches=0,
                num_inliers=0,
                inlier_ratio=0.0,
                rmse_pixels=999.0,
                mean_residual_pixels=999.0,
                max_residual_pixels=999.0,
                spatial_coverage_score=0.0,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
            )
            return RegistrationResult(
                transformation_model=self.transformation_model,
                transform_matrix=None,
                matches=[],
                inliers=[],
                metrics=empty_metrics,
            )

        # Step 5: Uniform Feature Allocation & Clumping Rejection
        if self.enable_anms:
            ref_idx = self.anms.suppress(kps_ref_raw, resp_ref_raw, self.target_features)
            tgt_idx = self.anms.suppress(kps_tgt_raw, resp_tgt_raw, self.target_features)
            kps_ref = kps_ref_raw[ref_idx]
            kps_tgt = kps_tgt_raw[tgt_idx]
        else:
            ref_idx = self.spatial_allocator.allocate(kps_ref_raw, resp_ref_raw, norm_ref.shape, self.target_features)
            tgt_idx = self.spatial_allocator.allocate(kps_tgt_raw, resp_tgt_raw, norm_tgt.shape, self.target_features)
            kps_ref = kps_ref_raw[ref_idx]
            kps_tgt = kps_tgt_raw[tgt_idx]

        # Step 6: RIFT Descriptor Extraction
        pts_ref_list = [(float(x), float(y)) for (x, y) in kps_ref]
        pts_tgt_list = [(float(x), float(y)) for (x, y) in kps_tgt]

        desc_ref, valid_ref_kps = self.rift_extractor.compute_descriptors(pc_ref.orientation_max_idx, pts_ref_list)
        desc_tgt, valid_tgt_kps = self.rift_extractor.compute_descriptors(pc_tgt.orientation_max_idx, pts_tgt_list)

        # Step 7: Robust Descriptor Matching (MNN + Lowe's NNDR)
        initial_matches = self.matcher.match(desc_ref, valid_ref_kps, desc_tgt, valid_tgt_kps)

        if len(initial_matches) < 4:
            empty_metrics = RegistrationMetrics(
                num_detected_ref=len(kps_ref),
                num_detected_target=len(kps_tgt),
                num_initial_matches=len(initial_matches),
                num_inliers=0,
                inlier_ratio=0.0,
                rmse_pixels=999.0,
                mean_residual_pixels=999.0,
                max_residual_pixels=999.0,
                spatial_coverage_score=0.0,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
            )
            return RegistrationResult(
                transformation_model=self.transformation_model,
                transform_matrix=None,
                matches=initial_matches,
                inliers=[],
                metrics=empty_metrics,
            )

        # Step 8: Coarse Robust Transformation Fitting (USAC-MAGSAC++)
        coarse_matrix, coarse_inliers = self.usac_magsac.estimate_transformation(
            initial_matches, model=self.transformation_model
        )

        if len(coarse_inliers) < 4 or coarse_matrix is None:
            empty_metrics = RegistrationMetrics(
                num_detected_ref=len(kps_ref),
                num_detected_target=len(kps_tgt),
                num_initial_matches=len(initial_matches),
                num_inliers=len(coarse_inliers),
                inlier_ratio=float(len(coarse_inliers) / len(initial_matches)) if initial_matches else 0.0,
                rmse_pixels=999.0,
                mean_residual_pixels=999.0,
                max_residual_pixels=999.0,
                spatial_coverage_score=0.0,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
            )
            return RegistrationResult(
                transformation_model=self.transformation_model,
                transform_matrix=None,
                matches=initial_matches,
                inliers=[],
                metrics=empty_metrics,
            )

        # Step 9: Sub-Pixel Peak Refinement on Invariant Phase Congruency Moment Surface
        if self.enable_subpixel:
            refined_inliers = self.subpixel_refiner.refine_matches_batch(
                coarse_inliers, pc_ref.max_moment, pc_tgt.max_moment
            )
            src_pts = np.array([m.ref_xy for m in refined_inliers], dtype=np.float64)
            dst_pts = np.array([m.target_xy for m in refined_inliers], dtype=np.float64)

            # Re-estimate transformation on sub-pixel coordinates
            if self.transformation_model in [TransformationModel.AFFINE, TransformationModel.RIGID, TransformationModel.SIMILARITY]:
                mat_sub, mask_sub = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=0.55)
                if mat_sub is not None and mask_sub is not None and np.sum(mask_sub) >= 4:
                    refined_matrix = mat_sub
                    sub_mask = mask_sub.ravel().astype(bool)
                else:
                    refined_matrix = GeometricTransformationSolver.estimate_affine(src_pts, dst_pts)
                    src_h = np.hstack([src_pts, np.ones((len(src_pts), 1))])
                    pred_dst = src_h @ refined_matrix.T
                    res = np.linalg.norm(pred_dst - dst_pts, axis=1)
                    sub_mask = res <= 0.55
            elif self.transformation_model == TransformationModel.HOMOGRAPHY:
                mat_sub, mask_sub = cv2.findHomography(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=0.55)
                if mat_sub is not None and mask_sub is not None and np.sum(mask_sub) >= 4:
                    refined_matrix = mat_sub
                    sub_mask = mask_sub.ravel().astype(bool)
                else:
                    refined_matrix = GeometricTransformationSolver.estimate_homography(src_pts, dst_pts)
                    src_h = np.hstack([src_pts, np.ones((len(src_pts), 1))])
                    proj = (refined_matrix @ src_h.T).T
                    pred_dst = proj[:, :2] / (proj[:, 2:3] + 1e-8)
                    res = np.linalg.norm(pred_dst - dst_pts, axis=1)
                    sub_mask = res <= 0.55
            else:
                refined_matrix = coarse_matrix
                res = np.array([m.residual_error for m in refined_inliers if m.residual_error is not None])
                sub_mask = res <= 0.55
            if np.sum(sub_mask) >= 4:
                final_src = src_pts[sub_mask]
                final_dst = dst_pts[sub_mask]
                if self.transformation_model in [TransformationModel.AFFINE, TransformationModel.RIGID, TransformationModel.SIMILARITY]:
                    final_matrix = GeometricTransformationSolver.estimate_affine(final_src, final_dst)
                    src_h_sub = np.hstack([final_src, np.ones((len(final_src), 1))])
                    final_pred = src_h_sub @ final_matrix.T
                    final_res = np.linalg.norm(final_pred - final_dst, axis=1)
                elif self.transformation_model == TransformationModel.HOMOGRAPHY:
                    final_matrix = GeometricTransformationSolver.estimate_homography(final_src, final_dst)
                    src_h_sub = np.hstack([final_src, np.ones((len(final_src), 1))])
                    proj = (final_matrix @ src_h_sub.T).T
                    final_pred = proj[:, :2] / (proj[:, 2:3] + 1e-8)
                    final_res = np.linalg.norm(final_pred - final_dst, axis=1)
                else:
                    final_matrix = refined_matrix
                    final_res = res[sub_mask]

                final_inliers: List[KeypointMatch] = []
                sub_indices = np.where(sub_mask)[0]
                for k, idx in enumerate(sub_indices):
                    m = refined_inliers[idx]
                    final_inliers.append(
                        KeypointMatch(
                            ref_xy=m.ref_xy,
                            target_xy=m.target_xy,
                            confidence=m.confidence,
                            subpixel_refined=True,
                            residual_error=float(final_res[k]),
                        )
                    )
                matrix = final_matrix
                inliers = final_inliers
            else:
                matrix = refined_matrix
                inliers = refined_inliers
        else:
            matrix = coarse_matrix
            inliers = coarse_inliers

        # Step 10: Quantitative Metrics & Warping
        num_inliers = len(inliers)
        num_init = len(initial_matches)
        inlier_ratio = float(num_inliers / num_init) if num_init > 0 else 0.0

        if num_inliers >= 4 and matrix is not None:
            residuals = np.array([m.residual_error for m in inliers if m.residual_error is not None])
            rmse = float(np.sqrt(np.mean(residuals**2))) if len(residuals) > 0 else 0.0
            mean_res = float(np.mean(residuals)) if len(residuals) > 0 else 0.0
            max_res = float(np.max(residuals)) if len(residuals) > 0 else 0.0

            # Compute spatial dispersion score and Shannon entropy of inliers
            inlier_pts = np.array([m.ref_xy for m in inliers])
            coverage_score = self.spatial_allocator.compute_spatial_coverage(inlier_pts, norm_ref.shape)
            entropy_score = self.spatial_allocator.compute_spatial_uniformity_entropy(inlier_pts, norm_ref.shape)

            # Warp target into reference coordinates
            if self.transformation_model == TransformationModel.THIN_PLATE_SPLINE:
                tps = ThinPlateSplineTransformer(regularization=1e-4)
                src_inliers = np.array([m.target_xy for m in inliers], dtype=np.float32)
                dst_inliers = np.array([m.ref_xy for m in inliers], dtype=np.float32)
                tps.fit(dst_inliers, src_inliers)
                warped = tps.warp_image(norm_tgt, norm_ref.shape)
            else:
                warped = GeometricTransformationSolver.warp_image(
                    norm_tgt, matrix, self.transformation_model, norm_ref.shape
                )
        else:
            rmse = 999.0
            mean_res = 999.0
            max_res = 999.0
            coverage_score = 0.0
            entropy_score = 0.0
            warped = None

        proc_time = (time.perf_counter() - start_time) * 1000

        metrics = RegistrationMetrics(
            num_detected_ref=len(kps_ref),
            num_detected_target=len(kps_tgt),
            num_initial_matches=num_init,
            num_inliers=num_inliers,
            inlier_ratio=inlier_ratio,
            rmse_pixels=rmse,
            mean_residual_pixels=mean_res,
            max_residual_pixels=max_res,
            spatial_coverage_score=coverage_score,
            spatial_uniformity_entropy=entropy_score,
            processing_time_ms=proc_time,
        )

        return RegistrationResult(
            transformation_model=self.transformation_model,
            transform_matrix=matrix,
            matches=initial_matches,
            inliers=inliers,
            metrics=metrics,
            warped_target=warped,
        )
