#DVC (Data Version Control) & Model Training.

DVC official Link:

https://doc.dvc.org/start

Get a dataset from [https://archive.ics.uci.edu](https://archive.ics.uci.edu/datasets)/

I am taking Iris dataset

![image.png](attachment:a813c6cb-74d6-4e2b-b8b9-744944a6f82b:image.png)

```jsx
wget https://archive.ics.uci.edu/static/public/53/iris.zip
unzip iris.zip -d iris
```

The `.data` extension has the data inside it and the `.names`  has the information about the data.

```jsx
ubuntu@ubuntu-desktop:~/mlops/dataset/iris$ ls
*bezdekIris.data  Index  iris.data  iris.names*
```

```jsx
ubuntu@ubuntu-desktop:~/mlops/dataset/iris$ cat iris.data 
5.1,3.5,1.4,0.2,Iris-setosa
4.9,3.0,1.4,0.2,Iris-setosa
4.7,3.2,1.3,0.2,Iris-setosa
4.6,3.1,1.5,0.2,Iris-setosa
see more...
```

Attribute Information:

1. sepal length in cm
2. sepal width in cm
3. petal length in cm
4. petal width in cm
5. class:
-- Iris Setosa
-- Iris Versicolour
-- Iris Virginica

**After the dataset gathered the next process is Data cleaning and Data Preprocessing / Preparation**

**But The Iris dataset is already cleaned and preprocessed. Here’s why:**

- No missing values – every row has values for all features.
- Numeric features – all four features (`sepal length`, `sepal width`, `petal length`, `petal width`) are numbers, no need for encoding.
- Categorical target is labeled – the species column has clear labels (`setosa`, `versicolor`, `virginica`).
- No duplicates – each row is a unique flower sample.

<aside>
💡

The dataset you download sometimes comes without headers. Adding them makes code easier to read.

If you load via `sklearn.datasets.load_iris()`, headers aren’t needed because feature names are included.

</aside>

**Lets add the header to the datasets and conevrt it to `.csv`  format, Because:**

- CSV is standard, easy-to-use format for ML libraries like pandas, scikit-learn, PyTorch, etc.
- Most ML code examples assume CSV files.
- It is human-readable, can be opened in Excel or any text editor.
- Supports DVC tracking easily (`dvc add dataset.csv`).

```jsx
cp iris.data iris.csv
```

Edit the `.csv`  file and add the headers.

Refer it from `.names` file.

```jsx
sepal length,sepal width,petal length,petal width,class
5.1,3.5,1.4,0.2,Iris-setosa
4.9,3.0,1.4,0.2,Iris-setosa
4.7,3.2,1.3,0.2,Iris-setosa
....
```

Save it and move it to your respected folder where you have you python and other files ( your intialized directory for git and dvc )

```jsx
mv ../dataset/iris/iris.csv data/
```

### **Set up your project structure**

In your project folder, create a structure like this:

```
mlops-iris/
├── data/
│   └── iris.csv
├── src/
│   └── train.py
├── .gitignore
├── requirements.txt
└── dvc.yaml# optional later if using DVC pipelines
```

# Install DVC

Create a virtual environment in python.

```jsx
python3 -m venv .venv
```

Activate `.venv` 

```jsx
source .venv/bin/activate
```

Install `DVC`

```jsx
python3 -m pip install dvc
```

## **Step 1: Initialize Git and DVC**

```bash
# Initialize Git
git init

# Initialize DVC
dvc init
```

> ✅ This prepares your project to track code and data separately.
> 

## **Step 2: Track your dataset with DVC**

Track the dataset with DVC

This  automatically creates a `iris.csv.dvc` for github to track the changes. And this file is a metadata file of the actual dataset which we will store in the github.

```bash
dvc add data/iris.csv
```

Add these to `.gitignore` file at the root level

```jsx
.git/
.venv/
iris.csv
```

**Add to Git**

```jsx
git add data/iris.csv.dvc .gitignore
git commit -m"Add Iris dataset with DVC tracking"
```

> Now DVC tracks your dataset without storing the full CSV in Git.
> 

## **Step 3: Create requirements file**

Create a file `requirements.txt` with the necessary packages:

```
pandas
scikit-learn
joblib
dvc
```

Install them:

```jsx
python3 -m pip install -r requirements.txt
```

## **Step 4: Create your training script**

Create `src/train.py`. This will:

1. Load the dataset
2. Split into features & target
3. Split into train/test
4. Train a model
5. Evaluate & save it

Here’s an example:

```jsx
# src/train.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Load dataset
data_path = os.path.join("data", "iris.csv")
df = pd.read_csv(data_path)

# Features and target
X = df[['sepal length', 'sepal width', 'petal length', 'petal width']]
y = df['class']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy*100:.2f}%")

# Save model
os.makedirs("models", exist_ok=True)
model_path = os.path.join("models", "iris_model.pkl")
joblib.dump(model, model_path)
print(f"Model saved at {model_path}")
```

Train the model:

```jsx
python3 src/train.py
```

Output:

```jsx
(.venv) ubuntu@ubuntu-desktop:~/mlops/mlops-iris$ python3 src/train.py 
Model accuracy: 100.00%
Model saved at models/iris_model.pkl
```

Check the model:

```jsx
(.venv) ubuntu@ubuntu-desktop:~/mlops/mlops-iris$ ls
data  models  requirements.txt  src
(.venv) ubuntu@ubuntu-desktop:~/mlops/mlops-iris$ ls models/
iris_model.pkl
```

## **Step 5: Track the trained model with DVC**

```bash
# Add the trained model to DVC
dvc add models/iris_model.pkl
```

> ✅ DVC now tracks both your dataset and your trained model versions.
> 

Add .pkl file to .gitignore

```jsx
*.pkl
```

Add the DVC file to Git

```jsx
git add models/iris_model.pkl.dvc
git commit -m"Add trained Decision Tree model"
```

Now Lets store/push the the model and dataset to s3.

Make sure you have a s3 bucket and aws cli configured and authentictaed to that account.

To check the authentication.

```jsx
aws sts get-caller-identity
```

```jsx
dvc remote add -d storage s3://iris-model-dataset/
```

Output:

```jsx
Setting 'storage' as a default remote.
```

Install `dvc_s3` module.

```jsx
python3 -m pip install dvc_s3
```

Now that a storage remote was configured, run `dvc push` to upload data:

```jsx
dvc push
```

Now it generates the remote config in the `.dvc/config` we have to add that to git as well. Then only cloning the code someone will get to know where the artifact is stored.

You can verify that using `git status` its modified by dvc

```jsx
cat .dvc/config 

[core]
    remote = storage
['remote "storage"']
    url = s3://iris-model-dataset/
```

```jsx
git add .dvc/config
git commit -m "add remote config"
```

Push to github

```jsx
git branch -M main
git remote add origin git@github.com:loks66/iris-model-training.git
git push -u origin main
```

Configs are stored in github

![image.png](attachment:d58e3360-c56f-4a91-a25a-dae5a551efc9:image.png)

Models and datastores are stored in S3.

![image.png](attachment:bc8173aa-35e1-4735-9dd5-183b09759688:image.png)

Lets Assume another (co-worker) will gather the code a model.

First they will clone git repo in their machine.

```jsx
git clone git@github.com:loks66/iris-model-training.git
```

then cd to the directory.And make sure activate the python venv and pull the model.

They should have the S3 access.

```jsx
python3 -m venv .venv
source .venv/bin/activate
```

```jsx
python3 -m pip install dvc
python3 -m pip install dvc_s3
```

```jsx
dvc pull
```

Output:

```jsx
Collecting                                                                                                                                             |2.00 [00:00,  111entry/s]
Fetching
Building workspace index                                                                                                                               |2.00 [00:00, 39.0entry/s]
Comparing indexes                                                                                                                                      |5.00 [00:00,  916entry/s]
Applying changes                                                                                                                                       |2.00 [00:00,   206file/s]
A       data/iris.csv
A       models/iris_model.pkl
2 files fetched and 2 files added

```

They will have the dataset and models in the respective folder. Previously it would be having only `.dvc` files Now after pulling we have `.csv` and `.pkl` files.

```jsx
(.venv) ubuntu@ubuntu-desktop:~/mlops/test/iris-model-training$ ls
*data  models  requirements.txt  src*
(.venv) ubuntu@ubuntu-desktop:~/mlops/test/iris-model-training$ ls models/
*iris_model.pkl  iris_model.pkl.dvc*
(.venv) ubuntu@ubuntu-desktop:~/mlops/test/iris-model-training$ ls data/
*iris.csv  iris.csv.dvc*
```

## **Step 6: Optional – Reproduce training later**

If you make changes to the code or dataset:

Lets say that user wants to add / remove some data into dataset and train the model again based on new dataset.

Lets edit the dataset (iris.csv) file.

The current iris dataset has 152 lines. For the sake of this tutorial i will remove lines make the data shorter and store that as new version.

`current dataset`

```jsx
cat data/iris.csv | wc -l
152
```

Lets edit and make it short:

```jsx
vi data/iris.csv
```

Now after removing i have only 30 lines

`New dataset`

```jsx
cat data/iris.csv | wc -l
30
```

Lets add the dataset to dvc and .dvc metadata file to git.

```jsx
dvc add data/iris.csv
git add data/iris.csv.dvc
git commit -m "add new dataset"
```

Now lets run the train.py to train the model.

Install the dependencies.

```jsx
python3 -m pip install -r requirements.txt
```

train the model

```jsx
python3 src/train.py
```

Output:

```jsx
Model accuracy: 100.00%
Model saved at models/iris_model.pkl
```

Now the new .dvc metadata file is generate you can compare them. Lets add them to github and add the models in dvc.

```bash
dvc add models/iris_model.pkl
git add models/iris_model.pkl.dvc
git commit -m"Retrain model with new code or data"
```

Push the git and dvc both to store the updated changes

```jsx
git push
dvc push
```

Now Lets you want go to the previos version of the model.

Do git log to identify the commit hash

![image.png](attachment:a75bb70b-7169-41fd-961f-7a04787dddbf:image.png)

Once you find out the commit has of the previous version, then do:

```jsx
git checkout a151f20e65715757db49f521f35a46273586eb71
```

Now do :

```jsx
dvc checkout
```

then 

```jsx
cat data/iris.csv
```

You would see the previous dataset is present..

```jsx
cat data/iris.csv | wc -l
152
```

To go back the latest one.

```jsx
git checkout main
dvc checkout
```

```jsx
cat data/iris.csv | wc -l
30
```

This way you can modify and create new versions and switch between version. dvc depends on git metadata file and based on that it fetches the artifacts.

TL;DR

> You can switch between versions with Git + DVC:
> 

```bash
git checkout <commit_hash>
dvc checkout
```

This restores the **exact dataset and model** for that commit.

<aside>
💡

To deactivate the venv in python use `deactivate` command

</aside>
