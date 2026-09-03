"""
Unit and Integration Tests for lunar_core/ui/app.py.
"""

from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pytest

from lunar_core.models import KeypointMatch
from lunar_core.ui.app import render_tie_point_correspondences


def test_render_tie_point_correspondences():
    """Verifies side-by-side tie-point correspondence plot generation."""
    src = np.random.uniform(0.1, 0.9, (100, 100)).astype(np.float32)
    ref = np.random.uniform(0.1, 0.9, (100, 100)).astype(np.float32)

    matches = [
        KeypointMatch(ref_xy=(20.0, 20.0), target_xy=(22.0, 21.0), confidence=0.95),
        KeypointMatch(ref_xy=(70.0, 30.0), target_xy=(71.0, 29.0), confidence=0.75),
        KeypointMatch(ref_xy=(40.0, 80.0), target_xy=(42.0, 78.0), confidence=0.45),
    ]

    fig = render_tie_point_correspondences(src, ref, matches, max_display=10)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_render_empty_correspondences():
    """Verifies handling when no matches are provided."""
    src = np.zeros((50, 50), dtype=np.float32)
    ref = np.zeros((50, 50), dtype=np.float32)
    fig = render_tie_point_correspondences(src, ref, [], max_display=10)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
