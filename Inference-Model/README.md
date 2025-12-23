# Inference/Prediction Model
In ML there are **two phases**:

1.  **Training** → create the model
2. **Inference (Prediction)** → use the saved model

We’ve already done **training**.

Now we’ll do **inference**.

## What does “running a model” mean?

It means:

- Load the saved `.pkl` file
- Give it new input data
- Get predictions

Just like:

- Build Docker image → **run container**
- Train model → **run inference**

## Step-by-step: How to run your stored model

### 1. Make sure the model exists locally

From project root:

```bash
ls models/
```

You should see:

```
iris_model.pkl
```

If not (for example, fresh machine or old commit):

```bash
dvc pull
```

This downloads the model from **S3**.

---

### 2. Create a new file for inference

Create a new file:

```bash
vi src/predict.py
```

This file is ONLY for using the model (not training).

---

### 3. Write the inference code.

Paste this:

```python
import joblib
import pandas as pd
import os

# Load the trained model
model_path = os.path.join("models","iris_model.pkl")
model = joblib.load(model_path)

# Example: new flower data (same features as training)
sample = pd.DataFrame(
    [[5.1,3.5,1.4,0.2]],
    columns=["sepal length","sepal width","petal length","petal width"]
)

# Make prediction
prediction = model.predict(sample)

print("Predicted class:", prediction[0])
```

---

**What is happening here.**

**`joblib.load(...)`**

- Loads the trained model from disk
- Same model you trained earlier

**`sample`**

- This is **new unseen data**
- Must have:
    - Same features
    - Same order
    - Same column names

**`model.predict(sample)`**

- Runs inference
- Outputs predicted class:
    - `Iris-setosa`
    - `Iris-versicolor`
    - `Iris-virginica`

---

### 4. Run the model (IMPORTANT: from project root)

```bash
python3 src/predict.py
```

Expected output:

```bash
Predicted class: Iris-setosa
```

Now lets change the value in the python file something else and see what it predicts.

```jsx
sample = pd.DataFrame(
    [[2,6,5,1]],
    columns=["sepal length","sepal width","petal length","petal width"]
)
```

```bash
Predicted class: Iris-virginica
```

🎉 You just **ran a trained ML model**.

---

## Very important ML rule (memorize this)

> Training and inference must use the SAME feature schema.
> 

Same:

- Column names
- Order
- Data type

This is why ML pipelines break in production.

---

### How DVC helps here (key MLOps insight)

Because the model is tracked by DVC:

```bash
git checkout <old-commit>
dvc checkout
python3 src/predict.py
```

👉 You’ll run **the old model**, not the new one.

This gives:

- Reproducibility
- Debugging ability
- Audit trail

---

### Where this goes in real systems

This `predict.py` logic later becomes:

- REST API (FastAPI)
- Batch job
- Streaming consumer
- Kubernetes service

But the **core logic stays the same**.

---

## Final mental model (lock this in)

```
train.py   → creates model
model.pkl  → stored artifact
predict.py → uses model
DVC        → versions model
S3         → stores model
```
