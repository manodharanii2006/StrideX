
import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder

# -----------------------------
# Project paths
# -----------------------------
project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

dataset_path = os.path.join(
    project_root,
    "data",
    "synthetic",
    "gait_dataset.csv"
)

# -----------------------------
# Load dataset
# -----------------------------
df = pd.read_csv(dataset_path)

X = df.drop(columns=["risk"])
y = df["risk"]

# Encode labels for XGBoost
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.3,
    random_state=42,
    stratify=y_encoded,
)

# -----------------------------
# Random Forest
# -----------------------------
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)

rf_acc = accuracy_score(y_test, rf_pred)
rf_f1 = f1_score(y_test, rf_pred, average="weighted")

# -----------------------------
# XGBoost
# -----------------------------
xgb = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective="multi:softmax",
    num_class=3,
    random_state=42,
)

xgb.fit(X_train, y_train)

xgb_pred = xgb.predict(X_test)

xgb_acc = accuracy_score(y_test, xgb_pred)
xgb_f1 = f1_score(y_test, xgb_pred, average="weighted")

# -----------------------------
# Compare
# -----------------------------
print("\n===== MODEL COMPARISON =====")
print(f"Random Forest Accuracy : {rf_acc:.3f}")
print(f"Random Forest F1       : {rf_f1:.3f}")

print(f"\nXGBoost Accuracy       : {xgb_acc:.3f}")
print(f"XGBoost F1             : {xgb_f1:.3f}")

# Save best model
if xgb_acc >= rf_acc:
    best_model = xgb
    model_name = "XGBoost"
else:
    best_model = rf
    model_name = "Random Forest"

model_path = os.path.join(project_root, "ai", "models", "model.pkl")
joblib.dump(best_model, model_path)

print(f"\nBest Model: {model_name}")
print(f"Saved to: {model_path}")