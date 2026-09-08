import os
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from django.conf import settings
from apps.ml_engine.utils.model_trainer import train_and_save_initial_models


class MLPredictorService:
    """Service handling ML inference using serialized LightGBM models."""

    def __init__(self):
        self.models_dir = getattr(settings, 'MODELS_DIR', './models')
        self.clf_model = None
        self.reg_model = None
        self._load_or_initialize_models()

    def _load_or_initialize_models(self):
        """Loads serialized LightGBM models or trains default baselines if absent."""
        clf_path = os.path.join(self.models_dir, 'lgbm_classifier.joblib')
        reg_path = os.path.join(self.models_dir, 'lgbm_regressor.joblib')

        if not (os.path.exists(clf_path) and os.path.exists(reg_path)):
            clf_path, reg_path = train_and_save_initial_models(self.models_dir)

        try:
            self.clf_model = joblib.load(clf_path)
            self.reg_model = joblib.load(reg_path)
        except Exception as e:
            print(f"[ML Engine Warning] Failed to load joblib models ({e}). Retraining initial models...")
            clf_path, reg_path = train_and_save_initial_models(self.models_dir)
            self.clf_model = joblib.load(clf_path)
            self.reg_model = joblib.load(reg_path)

    def predict_simulation(
        self,
        promedio_general: float,
        horas_trabajo_semanal: float,
        horas_sueno_objetivo: float,
        subjects_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes LightGBM classifier & regressor for selected subjects and student profile.

        subjects_data format:
        [
            {
                'id': 1,
                'nombre': 'Análisis Matemático I',
                'codigo': 'MAT101',
                'promedio_historico_promocion': 6.5,
                'horas_cursada_semanal': 6.0
            },
            ...
        ]
        """
        cantidad_materias = len(subjects_data)
        if cantidad_materias == 0:
            return {
                'materias_predicciones': [],
                'horas_estudio_sugeridas_dia': 0.0,
                'alerta_sobrecarga': False,
                'nivel_riesgo': 'Bajo',
                'resumen_horas_semanales': {
                    'horas_cursada': 0.0,
                    'horas_estudio': 0.0,
                    'horas_trabajo': horas_trabajo_semanal,
                    'horas_sueno': horas_sueno_objetivo * 7,
                    'horas_totales_ocupadas': horas_trabajo_semanal + (horas_sueno_objetivo * 7)
                }
            }

        # Build feature DataFrames for model evaluation
        feature_rows = []
        total_horas_cursada = sum(s['horas_cursada_semanal'] for s in subjects_data)

        for subj in subjects_data:
            feature_rows.append({
                'promedio_general': float(promedio_general),
                'horas_trabajo_semanal': float(horas_trabajo_semanal),
                'horas_sueno_objetivo': float(horas_sueno_objetivo),
                'promedio_historico_promocion': float(subj['promedio_historico_promocion']),
                'horas_cursada_semanal': float(subj['horas_cursada_semanal']),
                'cantidad_materias': cantidad_materias
            })

        df_features = pd.DataFrame(feature_rows)

        # 1. Classification: Probability of promotion per subject
        if hasattr(self.clf_model, 'predict_proba'):
            probabilities = self.clf_model.predict_proba(df_features)[:, 1]
        else:
            # Deterministic fallback logic if classifier is non-standard
            probabilities = np.clip(
                (df_features['promedio_general'] * 0.5 + df_features['promedio_historico_promocion'] * 0.5) / 10.0,
                0.1, 0.99
            ).values

        # 2. Regression: Recommended daily study hours per subject
        if hasattr(self.reg_model, 'predict'):
            study_hours_per_subject = self.reg_model.predict(df_features)
        else:
            study_hours_per_subject = (df_features['horas_cursada_semanal'] / 7.0) * 1.2

        # Aggregate metrics
        materias_predicciones = []
        for idx, subj in enumerate(subjects_data):
            prob = float(probabilities[idx])
            hours_day = max(0.5, float(study_hours_per_subject[idx]))
            materias_predicciones.append({
                'subject_id': subj['id'],
                'nombre': subj['nombre'],
                'codigo': subj.get('codigo', ''),
                'probabilidad_promocion': round(prob, 4),
                'porcentaje_promocion': f"{round(prob * 100, 1)}%",
                'horas_estudio_sugeridas_dia_materia': round(hours_day, 2)
            })

        # Total recommended study hours per day (sum or global model estimate)
        horas_estudio_sugeridas_dia = round(float(np.sum(study_hours_per_subject)), 2)
        horas_estudio_semanales_totales = horas_estudio_sugeridas_dia * 7.0

        # 3. Overload Traffic Light calculation
        # formula: horas_cursada + horas_estudio + horas_trabajo + (horas_sueno * 7) > 168
        horas_sueno_semanales = float(horas_sueno_objetivo) * 7.0
        horas_totales_comprometidas = (
            total_horas_cursada +
            horas_estudio_semanales_totales +
            float(horas_trabajo_semanal) +
            horas_sueno_semanales
        )

        alerta_sobrecarga = horas_totales_comprometidas > 168.0

        # Determine overall risk level ('Bajo', 'Equilibrado', 'Alto')
        avg_prob = float(np.mean(probabilities))
        if alerta_sobrecarga or avg_prob < 0.45 or horas_totales_comprometidas > 150.0:
            nivel_riesgo = 'Alto'
        elif avg_prob < 0.70 or horas_totales_comprometidas > 120.0:
            nivel_riesgo = 'Equilibrado'
        else:
            nivel_riesgo = 'Bajo'

        return {
            'materias_predicciones': materias_predicciones,
            'horas_estudio_sugeridas_dia': horas_estudio_sugeridas_dia,
            'alerta_sobrecarga': alerta_sobrecarga,
            'nivel_riesgo': nivel_riesgo,
            'promedio_probabilidad_promocion': round(avg_prob, 4),
            'resumen_horas_semanales': {
                'horas_cursada': round(total_horas_cursada, 2),
                'horas_estudio': round(horas_estudio_semanales_totales, 2),
                'horas_trabajo': round(float(horas_trabajo_semanal), 2),
                'horas_sueno': round(horas_sueno_semanales, 2),
                'horas_totales_ocupadas': round(horas_totales_comprometidas, 2),
                'horas_libres_disponibles': round(max(0.0, 168.0 - horas_totales_comprometidas), 2)
            }
        }
