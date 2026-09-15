
import random


def simulate_sensor_data(scenario="NORMAL"):
    """
    Simulated Sensor Data — Prototype
    Generates wearable-like values for ML training.
    """

    if scenario == "NORMAL":
        return {
            "left_pressure": round(random.uniform(48, 52), 1),
            "right_pressure": round(random.uniform(48, 52), 1),
            "pressure_imbalance": round(random.uniform(0, 4), 1),
            "acc_x": round(random.uniform(-0.3, 0.3), 2),
            "acc_y": round(random.uniform(0.8, 1.2), 2),
            "acc_z": round(random.uniform(-0.3, 0.3), 2),
            "gyro_x": round(random.uniform(-5, 5), 1),
            "gyro_y": round(random.uniform(-5, 5), 1),
            "gyro_z": round(random.uniform(-5, 5), 1),
            "foot_loading": round(random.uniform(95, 105), 1),
            "sensor_step_variability": round(random.uniform(0.01, 0.04), 3),
        }

    elif scenario == "ASYMMETRIC":
        return {
            "left_pressure": round(random.uniform(60, 70), 1),
            "right_pressure": round(random.uniform(30, 40), 1),
            "pressure_imbalance": round(random.uniform(20, 35), 1),
            "acc_x": round(random.uniform(-0.6, 0.6), 2),
            "acc_y": round(random.uniform(0.8, 1.3), 2),
            "acc_z": round(random.uniform(-0.6, 0.6), 2),
            "gyro_x": round(random.uniform(-15, 15), 1),
            "gyro_y": round(random.uniform(-15, 15), 1),
            "gyro_z": round(random.uniform(-15, 15), 1),
            "foot_loading": round(random.uniform(80, 120), 1),
            "sensor_step_variability": round(random.uniform(0.05, 0.10), 3),
        }

    elif scenario == "UNSTABLE":
        return {
            "left_pressure": round(random.uniform(35, 65), 1),
            "right_pressure": round(random.uniform(35, 65), 1),
            "pressure_imbalance": round(random.uniform(10, 25), 1),
            "acc_x": round(random.uniform(-1.2, 1.2), 2),
            "acc_y": round(random.uniform(0.5, 1.6), 2),
            "acc_z": round(random.uniform(-1.2, 1.2), 2),
            "gyro_x": round(random.uniform(-30, 30), 1),
            "gyro_y": round(random.uniform(-30, 30), 1),
            "gyro_z": round(random.uniform(-30, 30), 1),
            "foot_loading": round(random.uniform(70, 130), 1),
            "sensor_step_variability": round(random.uniform(0.08, 0.18), 3),
        }

    elif scenario == "IRREGULAR":
        return {
            "left_pressure": round(random.uniform(30, 70), 1),
            "right_pressure": round(random.uniform(30, 70), 1),
            "pressure_imbalance": round(random.uniform(15, 30), 1),
            "acc_x": round(random.uniform(-1.5, 1.5), 2),
            "acc_y": round(random.uniform(0.4, 1.8), 2),
            "acc_z": round(random.uniform(-1.5, 1.5), 2),
            "gyro_x": round(random.uniform(-40, 40), 1),
            "gyro_y": round(random.uniform(-40, 40), 1),
            "gyro_z": round(random.uniform(-40, 40), 1),
            "foot_loading": round(random.uniform(60, 140), 1),
            "sensor_step_variability": round(random.uniform(0.10, 0.22), 3),
        }

    else:
        raise ValueError("Unknown scenario")