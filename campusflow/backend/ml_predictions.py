"""Phase 11: explainable score forecasting lab.

No third-party student data is sent away. The real model trains only on explicitly
entered historical pairs (previous result, attendance before next assessment,
subsequent actual result), rather than falsely treating existing averages as
future-outcome labels. Demo mode uses synthetic examples and never writes rows.
"""
from __future__ import annotations

import random
from collections import Counter

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MIN_EXAMPLES = 12
MIN_STUDENTS = 4


def setup_prediction_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS performance_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            previous_score REAL NOT NULL CHECK (previous_score BETWEEN 0 AND 100),
            attendance_rate REAL NOT NULL CHECK (attendance_rate BETWEEN 0 AND 100),
            next_score REAL NOT NULL CHECK (next_score BETWEEN 0 AND 100),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_performance_student ON performance_examples(student_id);
    """)


def examples(conn):
    return [dict(r) for r in conn.execute("""
        SELECT e.id,e.student_id,s.name AS student_name,e.previous_score,
               e.attendance_rate,e.next_score,e.created_at
        FROM performance_examples e JOIN students s ON s.id=e.student_id
        ORDER BY e.id DESC
    """).fetchall()]


def demo_examples():
    """Fictional, reproducible data - never written to SQLite."""
    rng = random.Random(116)
    output = []
    for i in range(84):
        previous = round(rng.uniform(36, 96), 1)
        attendance = round(rng.uniform(44, 100), 1)
        subsequent = min(100, max(0, round(0.68 * previous + 0.25 * attendance + 4 + rng.gauss(0, 5), 1)))
        output.append({"student_id": i // 3 + 1, "previous_score": previous,
                       "attendance_rate": attendance, "next_score": subsequent})
    return output


def readiness(rows):
    unique = len({r["student_id"] for r in rows})
    count = len(rows)
    messages = []
    if count < MIN_EXAMPLES:
        messages.append(f"Add at least {MIN_EXAMPLES - count} more historical examples.")
    if unique < MIN_STUDENTS:
        messages.append(f"Add examples from at least {MIN_STUDENTS - unique} more distinct students.")
    labels = [float(row["next_score"]) for row in rows]
    if count >= MIN_EXAMPLES and unique >= MIN_STUDENTS and len({round(x, 4) for x in labels}) < 2:
        messages.append("Historical next scores must vary to train a useful model.")
    return {"ready": not messages, "examples": count, "students": unique,
            "minimum_examples": MIN_EXAMPLES, "minimum_students": MIN_STUDENTS,
            "requirements": messages}


def model_for(rows):
    check = readiness(rows)
    if not check["ready"]:
        return None
    x = np.array([[float(r["previous_score"]), float(r["attendance_rate"])] for r in rows])
    y = np.array([float(r["next_score"]) for r in rows])
    groups = np.array([int(r["student_id"]) for r in rows])
    # Hold out whole students to reduce within-student leakage between train/test.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=17)
    train_idx, test_idx = next(splitter.split(x, y, groups))
    if len(train_idx) < 3 or len(test_idx) < 1:
        return None
    evaluation_model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    evaluation_model.fit(x[train_idx], y[train_idx])
    predicted = np.clip(evaluation_model.predict(x[test_idx]), 0, 100)
    mae = round(float(mean_absolute_error(y[test_idx], predicted)), 1)
    baseline_mae = round(float(mean_absolute_error(y[test_idx], x[test_idx, 0])), 1)
    final_model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    final_model.fit(x, y)
    return final_model, {"mae": mae, "baseline_mae": baseline_mae,
                         "test_count": len(test_idx), "train_count": len(train_idx),
                         "algorithm": "Ridge regression", "evaluation": "Holdout by student"}


def overview(conn):
    entries = examples(conn)
    status = readiness(entries)
    trained = model_for(entries)
    return {**status, "evaluation": trained[1] if trained else None,
            "features": ["Previous assessment score", "Attendance before next assessment"],
            "target": "Next actual assessment score", "example_rows": entries,
            "demo": {"examples": len(demo_examples()), "type": "Synthetic sample data", "ready": True},
            "limitations": "Exploratory educational estimate, not an official grade or an assessment of ability. Small datasets can be unreliable."}


def predict(rows, previous_score, attendance_rate, mode):
    demo = mode == "demo"
    data = demo_examples() if demo else rows
    output = model_for(data)
    if output is None:
        return None
    model, evaluation = output
    value = float(np.clip(model.predict([[previous_score, attendance_rate]])[0], 0, 100))
    return {"mode": mode, "estimated_next_score": round(value, 1),
            "inputs": {"previous_score": previous_score, "attendance_rate": attendance_rate},
            "evaluation": evaluation,
            "disclaimer": ("DEMO ONLY: Model trained entirely on invented sample outcomes. "
                           "This number is not a prediction about any real student." if demo else
                           "Exploratory estimate based on recorded historical outcomes; not a guaranteed grade, risk label, or basis for high-stakes decisions."),
            "details": "Uses previous result and attendance only; other factors affecting learning and assessment outcomes are not modeled."}
