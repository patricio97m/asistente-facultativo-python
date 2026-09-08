import os
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from django.conf import settings


def generate_synthetic_dataset(n_samples: int = 1000, seed: int = 42):
    """Generates synthetic dataset to train initial LightGBM baseline models."""
    np.random.seed(seed)

    promedio_general = np.random.uniform(4.0, 10.0, n_samples)
    horas_trabajo_semanal = np.random.uniform(0, 45, n_samples)
    horas_sueno_objetivo = np.random.uniform(5, 9, n_samples)
    promedio_historico_promocion = np.random.uniform(4.0, 10.0, n_samples)
    horas_cursada_semanal = np.random.uniform(4, 28, n_samples)
    cantidad_materias = np.random.randint(1, 6, n_samples)

    X = pd.DataFrame({
        'promedio_general': promedio_general,
        'horas_trabajo_semanal': horas_trabajo_semanal,
        'horas_sueno_objetivo': horas_sueno_objetivo,
        'promedio_historico_promocion': promedio_historico_promocion,
        'horas_cursada_semanal': horas_cursada_semanal,
        'cantidad_materias': cantidad_materias
    })

    # Linear combination to derive target probability and study hours
    score = (
        0.35 * X['promedio_general'] +
        0.35 * X['promedio_historico_promocion'] -
        0.05 * X['horas_trabajo_semanal'] -
        0.08 * X['horas_cursada_semanal'] +
        np.random.normal(0, 0.5, n_samples)
    )

    # Sigmoid normalization for binary promotion outcome
    prob = 1 / (1 + np.exp(- (score - 4.5)))
    y_class = (prob >= 0.50).astype(int)

    # Estimated study hours per day required (clamped between 1 and 7)
    raw_study_hours = (
        (X['horas_cursada_semanal'] / 7.0) * 1.2 +
        (10.0 - X['promedio_general']) * 0.25 +
        (10.0 - X['promedio_historico_promocion']) * 0.2
    )
    y_reg = np.clip(raw_study_hours + np.random.normal(0, 0.3, n_samples), 1.0, 8.0)

    return X, y_class, y_reg


def train_and_save_initial_models(models_dir=None):
    """Trains and serializes initial LightGBM models if they don't exist."""
    if models_dir is None:
        models_dir = getattr(settings, 'MODELS_DIR', './models')

    os.makedirs(models_dir, exist_ok=True)
    clf_path = os.path.join(models_dir, 'lgbm_classifier.joblib')
    reg_path = os.path.join(models_dir, 'lgbm_regressor.joblib')

    if os.path.exists(clf_path) and os.path.exists(reg_path):
        return clf_path, reg_path

    print("[ML Engine] Serialized models not found. Training initial baseline LightGBM models...")
    X, y_class, y_reg = generate_synthetic_dataset()

    clf = LGBMClassifier(
        n_estimators=50,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
        verbosity=-1
    )
    clf.fit(X, y_class)

    reg = LGBMRegressor(
        n_estimators=50,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
        verbosity=-1
    )
    reg.fit(X, y_reg)

    joblib.dump(clf, clf_path)
    joblib.dump(reg, reg_path)

    print(f"[ML Engine] Models saved successfully to {models_dir}")
    return clf_path, reg_path
