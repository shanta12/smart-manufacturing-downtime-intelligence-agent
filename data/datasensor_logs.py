# data/sensor_logs.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sensor_logs(num_machines=5, days=30):
    """
    Generates fake sensor data from 5 factory machines.
    Machine M002 is made to look like it is failing
    so our AI agent can detect and report it.
    """

    machines = [
        {"id": "M001", "name": "CNC Machine A",     "type": "CNC"},
        {"id": "M002", "name": "Conveyor Belt B",   "type": "Conveyor"},
        {"id": "M003", "name": "Robotic Arm C",     "type": "Robot"},
        {"id": "M004", "name": "Hydraulic Press D", "type": "Press"},
        {"id": "M005", "name": "Assembly Unit E",   "type": "Assembly"},
    ]

    logs       = []
    start_date = datetime.now() - timedelta(days=days)

    for machine in machines:
        for hour in range(days * 24):
            timestamp = start_date + timedelta(hours=hour)

            # M002 starts showing failure signs after 70% of time
            is_failing = (
                machine["id"] == "M002" and
                hour > (days * 24 * 0.7)
            )

            temperature = round(
                np.random.normal(92 if is_failing else 72, 5), 2
            )
            vibration = round(
                np.random.normal(9.5 if is_failing else 4.0, 1.2), 2
            )
            pressure = round(
                np.random.normal(78 if is_failing else 102, 8), 2
            )
            rpm = round(
                np.random.normal(1100 if is_failing else 1500, 100), 2
            )
            error_code = (
                random.choice(["E001", "E002", "NONE"])
                if is_failing else "NONE"
            )

            logs.append({
                "machine_id":   machine["id"],
                "machine_name": machine["name"],
                "machine_type": machine["type"],
                "timestamp":    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature":  temperature,
                "vibration":    vibration,
                "pressure":     pressure,
                "rpm":          rpm,
                "error_code":   error_code,
                "is_anomaly":   is_failing
            })

    df = pd.DataFrame(logs)
    print(f"✅ Generated {len(df)} sensor log records")
    return df


def generate_maintenance_history():
    """
    Returns past maintenance records for each machine.
    This helps the AI understand recurring problems.
    """

    history = [
        {
            "machine_id":       "M001",
            "maintenance_date": "2024-10-15",
            "type":             "Preventive",
            "description":      "Oil change and belt inspection",
            "technician":       "Rajesh Kumar",
            "vendor":           "Siemens",
            "cost":             1500,
            "downtime_hours":   4
        },
        {
            "machine_id":       "M002",
            "maintenance_date": "2024-09-20",
            "type":             "Corrective",
            "description":      "Bearing replacement due to vibration",
            "technician":       "Suresh Patil",
            "vendor":           "ABB",
            "cost":             3200,
            "downtime_hours":   8
        },
        {
            "machine_id":       "M002",
            "maintenance_date": "2024-11-01",
            "type":             "Corrective",
            "description":      "Motor overheating issue fixed",
            "technician":       "Suresh Patil",
            "vendor":           "ABB",
            "cost":             2800,
            "downtime_hours":   6
        },
        {
            "machine_id":       "M003",
            "maintenance_date": "2024-10-28",
            "type":             "Preventive",
            "description":      "Lubrication and calibration",
            "technician":       "Amit Sharma",
            "vendor":           "FANUC",
            "cost":             900,
            "downtime_hours":   2
        },
        {
            "machine_id":       "M004",
            "maintenance_date": "2024-11-10",
            "type":             "Preventive",
            "description":      "Hydraulic fluid replacement",
            "technician":       "Rajesh Kumar",
            "vendor":           "Bosch",
            "cost":             1200,
            "downtime_hours":   3
        },
    ]

    df = pd.DataFrame(history)
    print(f"✅ Generated {len(df)} maintenance history records")
    return df