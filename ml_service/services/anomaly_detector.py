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

# ==========================================
# OOP: Inheritance & Encapsulation
# ==========================================
class IsolationForestDetector(BaseAnomalyDetector):
    def __init__(self):
        # Encapsulation: Private attributes
        self.__model = IsolationForest(contamination=0.05, random_state=42)
        self.__is_trained = False
        
        # DSA: Priority Queue (Min-Heap) to track Top K most severe anomalies (lowest scores)
        self.__top_anomalies_heap = []
        self.__max_heap_size = 5
        
        # DSA: LRU Cache to memoize duplicate telemetry calculations
        self.__cache = LRUCache(capacity=100)

    def train(self, historical_data: List[Dict]):
        if not historical_data:
            return
            
        df = pd.DataFrame(historical_data)
        features = df[['rmse', 'spatial_entropy', 'inlier_ratio']]
        self.__model.fit(features)
        self.__is_trained = True

    def predict(self, current_telemetry: Dict) -> Dict:
        if not self.__is_trained:
            return {"status": "model_not_trained"}
            
        # O(1) Cache Lookup
        cache_key = f"{current_telemetry['rmse']}_{current_telemetry['spatial_entropy']}_{current_telemetry['inlier_ratio']}"
        cached_result = self.__cache.get(cache_key)
        if cached_result:
            return cached_result
        
        X = np.array([[
            current_telemetry['rmse'], 
            current_telemetry['spatial_entropy'], 
            current_telemetry['inlier_ratio']
        ]])
        
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
        
    # Getter method (Encapsulation)
    def get_top_anomalies(self) -> List[Dict]:
        """Returns the top K most severe anomalies using the internal Heap data structure."""
        # Sort the heap by score (lowest first) before returning
        sorted_anomalies = sorted(self.__top_anomalies_heap, key=lambda x: x[0])
        return [{"score": s, "telemetry": t} for s, t in sorted_anomalies]
