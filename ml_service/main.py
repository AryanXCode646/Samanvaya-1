from fastapi import FastAPI
from services.anomaly_detector import IsolationForestDetector
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Samanvaya ML Service")
detector = IsolationForestDetector()

# Dummy training for now
detector.train([
    {"rmse": 0.2, "spatial_entropy": 0.95, "inlier_ratio": 0.8},
    {"rmse": 0.3, "spatial_entropy": 0.90, "inlier_ratio": 0.75}
])

class Telemetry(BaseModel):
    rmse: float
    spatial_entropy: float
    inlier_ratio: float

@app.get("/")
def read_root():
    return {"status": "ML Microservice is running securely"}

@app.post("/api/predict_anomaly")
def predict(telemetry: Telemetry):
    return detector.predict(telemetry.model_dump())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
