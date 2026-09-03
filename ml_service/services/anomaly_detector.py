import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

class AlignmentAnomalyDetector:
    def __init__(self):
        # Isolation Forest for unsupervised anomaly detection on telemetry
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False

    def train(self, historical_data: list[dict]):
        df = pd.DataFrame(historical_data)
        features = df[['rmse', 'spatial_entropy', 'inlier_ratio']]
        self.model.fit(features)
        self.is_trained = True

    def predict(self, current_telemetry: dict) -> dict:
        if not self.is_trained:
            return {"status": "model_not_trained"}
        
        X = np.array([[
            current_telemetry['rmse'], 
            current_telemetry['spatial_entropy'], 
            current_telemetry['inlier_ratio']
        ]])
        
        prediction = self.model.predict(X)[0]
        score = self.model.decision_function(X)[0]
        
        return {
            "is_anomaly": bool(prediction == -1),
            "confidence_score": float(score)
        }
