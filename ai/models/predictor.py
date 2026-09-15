import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# -----------------------------
# Project Root
# -----------------------------
project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

# -----------------------------
# Paths
# -----------------------------
model_path = os.path.join(project_root, "ai", "models", "model.pkl")
dataset_path = os.path.join(
    project_root,
    "data",
    "synthetic",
    "gait_dataset.csv"
)

# -----------------------------
# Load model and dataset
# -----------------------------
model = joblib.load(model_path)
df = pd.read_csv(dataset_path)

# Build label encoder using original labels
encoder = LabelEncoder()
encoder.fit(df["risk"])


# -----------------------------
# Prediction Function
# -----------------------------
def predict_risk(
    cadence,
    walking_speed,
    symmetry,
    knee_angle,
    hip_angle,
    step_variability,
    pressure_imbalance,
    pain_score,
):
    """
    Predict gait risk level.
    Returns HIGH, MEDIUM or LOW.
    """

    data = pd.DataFrame([{
        "cadence": cadence,
        "walking_speed": walking_speed,
        "symmetry": symmetry,
        "knee_angle": knee_angle,
        "hip_angle": hip_angle,
        "step_variability": step_variability,
        "pressure_imbalance": pressure_imbalance,
        "pain_score": pain_score,
    }])

    prediction = model.predict(data)[0]

    # If model returns encoded numbers (0,1,2), convert back
    if isinstance(prediction, (np.integer, int)):
        prediction = encoder.inverse_transform([int(prediction)])[0]

    return prediction


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":

    result = predict_risk(
        cadence=181,
        walking_speed=0.15,
        symmetry=98.3,
        knee_angle=130.6,
        hip_angle=118.0,
        step_variability=0.6033,
        pressure_imbalance=0.3,
        pain_score=2,
    )

    print("\n===== STRIDEX RISK PREDICTION =====")
    print("Predicted Risk:", result)