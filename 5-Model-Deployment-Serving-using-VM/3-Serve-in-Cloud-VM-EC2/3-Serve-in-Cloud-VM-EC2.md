# 3. Serve in Cloud VM (EC2) uisng systemd service.

Provision an EC2 instance, SSH into that instance and then run the below commands

Update the instance:

```bash
 sudo apt update
```

Download the dataset (Crop yeild dataset)from Kaagle using curl:

```bash
curl -L -o smart-crop-recommendation-dataset.zip  https://www.kaggle.com/api/v1/datasets/download/miadul/smart-crop-recommendation-dataset
```

Unzip the file:

```bash
sudo unzip smart-crop-recommendation-dataset.zip 
```

Verify dataset :

```bash
head data/crop-yield.csv 
```

Make sure python3 and venv is installed:

```bash
python3 --version
sudo apt install python3.12-venv

```

Create a directory and copy the dataset will add all the files in that directory

```bash
mkdir crop-yeild-ml
cd crop-yeild-ml/
```

Copy the dataset into the created direcotry:

```bash
cp -r ../data .
```

create a requirements.txt file:

```bash
  vi requirements.txt
```

Add these to the requirements.txt file:

```bash
pandas
scikit-learn
fastapi
uvicorn
numpy
joblib
```

Create a venv and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Add `train.py` file: 

```bash
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
```

Add `app.py` for the prediction and api:

```bash
from fastapi import FastAPI
import joblib
import pandas as pd

app = FastAPI(title="Crop Yield Prediction API")

pipeline = joblib.load("model/pipeline.pkl")

@app.post("/predict")
def predict(data: dict):
    df = pd.DataFrame([data])
    prediction = pipeline.predict(df)[0]
    return {
        "predicted_yield_ton_per_hectare": round(float(prediction), 2)
    }
```

This is the directory tree view for reference:

```bash
crop-yeild-ml
│   ├── __pycache__
│   │   └── app.cpython-312.pyc
│   ├── app.py
│   ├── data
│   │   └── crop-yield.csv
│   ├── model
│   │   └── pipeline.pkl
│   ├── requirements.txt
│   └── train.py
```

Install all the requirements from `requirements.txt`

```bash
python3 -m pip install -r requirements.txt 
```

Run the train.py to train the model.

```bash
python3 train.py
```

Expected Output:

```bash
RMSE: 1.15
Model pipeline saved
```

You would get the model output to the model directory :

```bash
ubuntu@Serving-ML-model:~/crop-yeild-ml$ ls model/
pipeline.pkl
```

Run the `app.py` :

```bash
python3 app.py
```

Run the ASGI:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Make sure port 8000 is opened in the SG

Now inference/predict the model:

```bash
 curl -X POST http://localhost:8000/predict   -H "Content-Type: application/json"   -d '{
    "N": 132,
    "P": 62,
    "K": 22,
    "Soil_pH": 6.35,
    "Soil_Moisture": 59.78,
    "Soil_Type": "Clay",
    "Organic_Carbon": 0.43,
    "Temperature": 22.97,
    "Humidity": 53.89,
    "Rainfall": 1305.68,
    "Sunlight_Hours": 7.73,
    "Wind_Speed": 15.96,
    "Region": "Central",
    "Altitude": 36,
    "Season": "Rabi",
    "Crop_Type": "Maize",
    "Irrigation_Type": "Canal",
    "Fertilizer_Used": 223.48,
    "Pesticide_Used": 23.36
  }'
```

Expected Output:

```bash
{"predicted_yield_ton_per_hectare":10.21}
```

Now the model is successfully deployed in the VM. 

You can also use public ip to predict the model instead of using localhost.

Next we will see how to deploy the model in the VM for production serve.