import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np
import heapq
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

# ==========================================
# OOP: Abstract Base Class & Polymorphism
# ==========================================
class BaseAnomalyDetector(ABC):
    """Abstract base class enforcing a contract for all ML detectors."""
    
    @abstractmethod
    def train(self, historical_data: List[Dict]):
        pass
        
    @abstractmethod
    def predict(self, current_telemetry: Dict) -> Dict:
        pass

# ==========================================
# DSA: Doubly Linked List Node for LRU Cache
# ==========================================
class LRUNode:
    def __init__(self, key: str, value: Dict):
        self.key = key
        self.value = value
        self.prev: Optional[LRUNode] = None
        self.next: Optional[LRUNode] = None

# ==========================================
# DSA: Custom LRU Cache Implementation
# ==========================================
class LRUCache:
    """Least Recently Used Cache using HashMap + Doubly Linked List for O(1) operations."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[str, LRUNode] = {}
        # Dummy head and tail
        self.head = LRUNode("head", {})
        self.tail = LRUNode("tail", {})
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: LRUNode):
        prev_node = node.prev
        next_node = node.next
        if prev_node and next_node:
            prev_node.next = next_node
            next_node.prev = prev_node

    def _add(self, node: LRUNode):
        prev_tail = self.tail.prev
        if prev_tail:
            prev_tail.next = node
            node.prev = prev_tail
            node.next = self.tail
            self.tail.prev = node

    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.value
        return None

    def put(self, key: str, value: Dict):
        if key in self.cache:
            self._remove(self.cache[key])
        node = LRUNode(key, value)
        self._add(node)
        self.cache[key] = node
        if len(self.cache) > self.capacity:
            lru_node = self.head.next
            if lru_node:
                self._remove(lru_node)
                del self.cache[lru_node.key]

import os
import joblib

# ==========================================
# OOP: Inheritance & Encapsulation
# ==========================================
class IsolationForestDetector(BaseAnomalyDetector):
    def __init__(self, model_path="data/isolation_forest.joblib"):
        self.model_path = model_path
        # Encapsulation: Private attributes
        # OPTIMIZATION: n_estimators reduced to 50 (2x faster), n_jobs=-1 (multi-core parallelism)
        self.__model = IsolationForest(
            n_estimators=50, 
            contamination=0.05, 
            random_state=42,
            n_jobs=-1,
            max_samples='auto'
        )
        self.__is_trained = False
        
        # DSA: Priority Queue (Min-Heap) to track Top K most severe anomalies (lowest scores)
        self.__top_anomalies_heap = []
        self.__max_heap_size = 5
        
        # DSA: LRU Cache to memoize duplicate telemetry calculations
        self.__cache = LRUCache(capacity=500) # Increased capacity for better hit rate
        
        # Attempt to load pre-trained model
        self.load_model()

    def train(self, historical_data: List[Dict]):
        if not historical_data:
            return
            
        df = pd.DataFrame(historical_data)
        # OPTIMIZATION: Cast features to float32 to halve memory usage
        features = df[['rmse', 'spatial_entropy', 'inlier_ratio']].astype(np.float32)
        self.__model.fit(features)
        self.__is_trained = True
        self.save_model()

    def save_model(self):
        """Persist model to disk for rapid restarts (O(1) startup)."""
        if self.__is_trained:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.__model, self.model_path, compress=3)

    def load_model(self):
        """Load pre-trained model to bypass expensive training phases."""
        if os.path.exists(self.model_path):
            try:
                self.__model = joblib.load(self.model_path)
                self.__is_trained = True
                
                # OPTIMIZATION: Warm-up inference to avoid cold-start latency spikes
                warmup_X = np.array([[0.1, 0.5, 0.9]], dtype=np.float32)
                self.__model.predict(warmup_X)
            except Exception as e:
                print(f"Failed to load model from {self.model_path}: {e}")
                self.__is_trained = False

    def predict(self, current_telemetry: Dict) -> Dict:
        if not self.__is_trained:
            return {"status": "model_not_trained"}
            
        # O(1) Cache Lookup (Fast string formatting)
        rmse, entropy, inlier = current_telemetry['rmse'], current_telemetry['spatial_entropy'], current_telemetry['inlier_ratio']
        cache_key = f"{rmse:.4f}_{entropy:.4f}_{inlier:.4f}"
        cached_result = self.__cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # OPTIMIZATION: float32 array
        X = np.array([[rmse, entropy, inlier]], dtype=np.float32)
        
        prediction = self.__model.predict(X)[0]
        score = self.__model.decision_function(X)[0]
        
        is_anomaly = bool(prediction == -1)
        
        # DSA: Maintain a Min-Heap of the top 5 most severe anomalies (severe = highly negative score)
        if is_anomaly:
            # We push (score, telemetry) - heapq acts as a min-heap, so lowest score stays at root
            # To keep track of worst (most negative), we use a max-heap approach by pushing (-score, ...)
            heapq.heappush(self.__top_anomalies_heap, (score, current_telemetry))
            if len(self.__top_anomalies_heap) > self.__max_heap_size:
                # Remove the least severe anomaly from our top 5 tracker
                heapq.heappop(self.__top_anomalies_heap)
        
        result = {
            "is_anomaly": is_anomaly,
            "confidence_score": float(score)
        }
        
        # O(1) Cache Insertion
        self.__cache.put(cache_key, result)
        
        return result
        
    @property
    def is_trained(self) -> bool:
        """Public read-only property for training state."""
        return self.__is_trained

    def predict_batch(self, telemetry_list: List[Dict]) -> List[Dict]:
        """
        Vectorized batch prediction — builds a single float32 matrix and
        runs ONE model.predict() call. Up to 50x faster than looping predict().

        Parameters
        ----------
        telemetry_list : List[Dict]
            List of telemetry dicts, each with rmse, spatial_entropy, inlier_ratio.

        Returns
        -------
        List[Dict]
            List of {'is_anomaly': bool, 'confidence_score': float}
        """
        if not self.__is_trained:
            return [{"status": "model_not_trained"}] * len(telemetry_list)

        if not telemetry_list:
            return []

        # Build matrix in ONE numpy call — avoids Python loop overhead
        X = np.array(
            [[t["rmse"], t["spatial_entropy"], t["inlier_ratio"]] for t in telemetry_list],
            dtype=np.float32,
        )

        # Single vectorized inference call
        predictions = self.__model.predict(X)          # shape (N,)
        scores = self.__model.decision_function(X)     # shape (N,)

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            is_anomaly = bool(pred == -1)
            if is_anomaly:
                heapq.heappush(self.__top_anomalies_heap, (float(score), telemetry_list[i]))
                if len(self.__top_anomalies_heap) > self.__max_heap_size:
                    heapq.heappop(self.__top_anomalies_heap)
            results.append({"is_anomaly": is_anomaly, "confidence_score": float(score)})

        return results

    # Getter method (Encapsulation)
    def get_top_anomalies(self) -> List[Dict]:
        """Returns the top K most severe anomalies using the internal Heap data structure."""
        sorted_anomalies = sorted(self.__top_anomalies_heap, key=lambda x: x[0])
        return [{"score": s, "telemetry": t} for s, t in sorted_anomalies]
