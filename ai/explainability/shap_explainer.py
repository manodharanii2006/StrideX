import os
import joblib
import shap
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Project paths
# -----------------------------
project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

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

X = df.drop(columns=["risk"])

# -----------------------------
# SHAP Explainer
# -----------------------------
explainer = shap.TreeExplainer(model)

# Explain first sample
shap_values = explainer.shap_values(X.iloc[[0]])

# -----------------------------
# Save summary plot
# -----------------------------
output_path = os.path.join(
    project_root,
    "ai",
    "explainability",
    "shap_summary.png"
)

plt.figure(figsize=(8, 5))

shap.summary_plot(
    shap_values,
    X.iloc[[0]],
    show=False
)

plt.tight_layout()
plt.savefig(output_path)
plt.close()

print("\n===== STRIDEX SHAP EXPLAINABILITY =====")
print("Explanation image saved to:")
print(output_path)