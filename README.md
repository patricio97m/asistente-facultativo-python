# Asistente Facultativo

Backend REST para la plataforma **Asistente Facultativo**, una herramienta impulsada por Machine Learning (**LightGBM**) que asiste a estudiantes universitarios en la planificación cuatrimestral y optimización de sus horarios de estudio.

## Tecnologías utilizadas

- **Lenguaje:** Python 3.11+
- **Framework Backend:** Django 5.1 & Django REST Framework (DRF)
- **Base de Datos:** SQLite3
- **Engine ML:** `lightgbm`, `scikit-learn`, `pandas`, `numpy`, `joblib`
- **Documentación de API:** `drf-spectacular` (OpenAPI 3.0 / Swagger UI)
- **Dockerización:** Docker & Docker Compose

---

## Instrucciones para ejecución rápida

### 1. Primera Ejecución Completa (Setup Inicial)

Para construir la imagen, levantar Docker en **segundo plano** (detached), aplicar migraciones y cargar los datos de prueba:

```bash
./init.sh
```

### 2. Ejecuciones Posteriores (Levantar Docker en Segundo Plano)

Para volver a iniciar los servicios en segundo plano:

```bash
./start.sh
```

*(Opcional)* Para ver los logs en tiempo real o crear un superusuario:

```bash
# Ver logs en vivo
docker compose logs -f

# Crear usuario administrador
docker compose exec web python manage.py createsuperuser
```

---

## Frontend Web Interactivo

El proyecto incluye un servicio de servidor estático ligero integrado en **Docker Compose** en el puerto `3000`.

Al ejecutar `./start.sh` o `./init.sh`, el frontend se levanta automáticamente en:
**`http://localhost:3000`**

### Funcionalidades que permite probar:
- **Perfil de Estudiante:** Editar horas de trabajo, sueño deseado y promedio general (`POST /api/v1/profile/`).
- **Selección de Materias:** Carga dinámica desde `/api/v1/subjects/` con presets de prueba (*Carga Equilibrada* vs *Sobrecarga de 7 materias*).
- **Simulación ML LightGBM:** Visualiza el semáforo de riesgo (`Bajo`, `Equilibrado`, `Alto`), el porcentaje de probabilidad de promoción por materia, las horas diarias recomendadas y el desglose de las 168 horas semanales.
- **Cronograma Semanal & Feedback:** Genera el plan día a día y permite registrar feedback en tiempo real.

---

## Documentación Interactiva (Swagger / ReDoc)

Una vez iniciado el servidor, se puede acceder a la documentación interactiva OpenAPI 3.0 en:

- **Swagger UI:** `http://localhost:8080/api/schema/swagger-ui/`
- **ReDoc:** `http://localhost:8080/api/schema/redoc/`
- **OpenAPI Schema (JSON):** `http://localhost:8080/api/schema/`

---

## Endpoints Principales

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/v1/profile/` | Crear / Actualizar perfil del estudiante |
| `GET` | `/api/v1/profile/` | Obtener perfil del estudiante actual |
| `GET` | `/api/v1/subjects/` | Listar materias disponibles con promedios históricos |
| `POST` | `/api/v1/simulations/predict/` | **Endpoint ML Principal:** Ejecuta modelos LightGBM y evalúa alerta de sobrecarga |
| `POST` | `/api/v1/study-plans/generate/` | Genera y guarda el cronograma semanal día a día |
| `POST` | `/api/v1/study-plans/{id}/feedback/` | Registra horas reales estudiadas y cumplimiento para reentrenamiento |

---

## Motor de ML y Modelos Serializados

- Al iniciar la aplicación, `apps.ml_engine.services.ml_service` comprueba la presencia de los modelos serializados en `./models/` (`lgbm_classifier.joblib` y `lgbm_regressor.joblib`).
- Si los archivos no existen, el sistema genera automáticamente un dataset sintético inicial y entrena los modelos baseline de **LightGBM** (`LGBMClassifier` y `LGBMRegressor`), guardándolos en el volumen persistente `./models/`.
