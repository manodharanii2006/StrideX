import os
import json

# -----------------------------
# Baseline File Path
# -----------------------------
project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

baseline_path = os.path.join(
    project_root,
    "data",
    "baseline",
    "baseline.json"
)


# -----------------------------
# Load Baseline
# -----------------------------
def load_baseline():
    with open(baseline_path, "r") as f:
        return json.load(f)


# -----------------------------
# Save Baseline
# -----------------------------
def save_baseline(data):
    with open(baseline_path, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# Compare Current vs Previous
# -----------------------------
def compare_to_baseline(current):
    baseline = load_baseline()

    if baseline["assessment_count"] == 0:
        current["assessment_count"] = 1
        save_baseline(current)
        return "First assessment recorded."

    comparison = {
        "cadence_change": round(current["cadence"] - baseline["cadence"], 2),
        "walking_speed_change": round(current["walking_speed"] - baseline["walking_speed"], 2),
        "symmetry_change": round(current["symmetry"] - baseline["symmetry"], 2),
        "knee_angle_change": round(current["knee_angle"] - baseline["knee_angle"], 2),
        "hip_angle_change": round(current["hip_angle"] - baseline["hip_angle"], 2),
        "step_variability_change": round(
            current["step_variability"] - baseline["step_variability"], 4
        ),
    }

    current["assessment_count"] = baseline["assessment_count"] + 1
    save_baseline(current)

    return comparison