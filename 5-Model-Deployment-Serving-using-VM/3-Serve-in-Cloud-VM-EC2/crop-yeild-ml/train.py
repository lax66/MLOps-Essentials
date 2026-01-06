import pandas as pd
import numpy as np
import joblib
import os

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Load data
df = pd.read_csv("data/crop-yield.csv")

X = df.drop("Crop_Yield_ton_per_hectare", axis=1)
y = df["Crop_Yield_ton_per_hectare"]

# Columns
categorical_cols = [
    "Soil_Type", "Region", "Season",
    "Crop_Type", "Irrigation_Type"
]

numerical_cols = [
    "N","P","K","Soil_pH","Soil_Moisture",
    "Organic_Carbon","Temperature","Humidity",
    "Rainfall","Sunlight_Hours","Wind_Speed",
    "Altitude","Fertilizer_Used","Pesticide_Used"
]

# Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", "passthrough", numerical_cols)
    ]
)

# Pipeline
pipeline = Pipeline([
    ("preprocess", preprocessor),
    ("model", RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    ))
])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train
pipeline.fit(X_train, y_train)

# Evaluate
preds = pipeline.predict(X_test)
mse = mean_squared_error(y_test, preds)
rmse = np.sqrt(mse)
print(f"RMSE: {rmse:.2f}")

# Save pipeline
os.makedirs("model", exist_ok=True)
joblib.dump(pipeline, "model/pipeline.pkl")
print("Model pipeline saved")

