from fastapi import FastAPI
import joblib
import pandas as pd

app = FastAPI(title="Crop Yield Prediction API")

pipeline = joblib.load("model/pipeline.pkl")
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/predict")
def predict(data: dict):
    df = pd.DataFrame([data])
    prediction = pipeline.predict(df)[0]
    return {
        "predicted_yield_ton_per_hectare": round(float(prediction), 2)
    }

