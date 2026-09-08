#!/usr/bin/env python3
"""
Test suite for live end-to-end API testing of Asistente Facultativo on http://localhost:8080
"""
import json
import sys
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8080/api/v1"


def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, json.loads(err_body) if err_body else {}


def print_section(title):
    print(f"\n=======================================================")
    print(f"  {title}")
    print(f"=======================================================")


def main():
    print("Iniciando pruebas E2E sobre el backend en Docker (http://localhost:8080)...\n")

    # 1. Test GET /profile/ and POST /profile/
    print_section("1. Test de Perfil de Estudiante (/profile/)")
    status_code, profile_get = make_request(f"{BASE_URL}/profile/")
    print(f"GET /profile/ -> Status: {status_code}")
    print(json.dumps(profile_get, indent=2, ensure_ascii=False))

    profile_payload = {
        "horas_trabajo_semanal": 22.0,
        "horas_sueno_objetivo": 8.0,
        "promedio_general": 8.1
    }
    status_code, profile_post = make_request(f"{BASE_URL}/profile/", method="POST", data=profile_payload)
    print(f"\nPOST /profile/ -> Status: {status_code}")
    print(json.dumps(profile_post, indent=2, ensure_ascii=False))

    # 2. Test GET /subjects/
    print_section("2. Test de Materias Disponibles (/subjects/)")
    status_code, subjects = make_request(f"{BASE_URL}/subjects/")
    print(f"GET /subjects/ -> Status: {status_code} ({len(subjects)} materias encontradas)")

    subject_ids = [s['id'] for s in subjects[:3]]
    print(f"Materias seleccionadas para simulación equilibrada: IDs {subject_ids}")

    # 3. Test POST /simulations/predict/ (Caso Equilibrado)
    print_section("3. Test de Predicción ML LightGBM (/simulations/predict/) - Caso Normal")
    predict_payload = {
        "subject_ids": subject_ids,
        "horas_trabajo_semanal": 20.0,
        "horas_sueno_objetivo": 8.0,
        "promedio_general": 8.0
    }
    status_code, prediction = make_request(f"{BASE_URL}/simulations/predict/", method="POST", data=predict_payload)
    print(f"POST /simulations/predict/ -> Status: {status_code}")
    print(json.dumps(prediction, indent=2, ensure_ascii=False))

    simulation_id = prediction.get("simulation_id")
    if not simulation_id:
        print("Error: No se obtuvo simulation_id")
        sys.exit(1)

    # 4. Test POST /simulations/predict/ (Caso de Sobrecarga Horaria / Alto Riesgo)
    print_section("4. Test de Predicción ML LightGBM - Caso de Sobrecarga (Alto Riesgo)")
    all_subject_ids = [s['id'] for s in subjects]
    overload_payload = {
        "subject_ids": all_subject_ids,
        "horas_trabajo_semanal": 48.0,  # 48 horas de trabajo
        "horas_sueno_objetivo": 8.0,    # 56 horas de sueño
        "promedio_general": 5.0
    }
    status_code, overload_pred = make_request(f"{BASE_URL}/simulations/predict/", method="POST", data=overload_payload)
    print(f"POST /simulations/predict/ (Sobrecarga) -> Status: {status_code}")
    print(f"Alerta Sobrecarga: {overload_pred.get('alerta_sobrecarga')}")
    print(f"Nivel Riesgo:     {overload_pred.get('nivel_riesgo')}")
    print(f"Resumen horas totales ocupadas: {overload_pred.get('resumen_horas_semanales', {}).get('horas_totales_ocupadas')}h / 168h")

    # 5. Test POST /study-plans/generate/
    print_section("5. Test de Generación de Cronograma Semanal (/study-plans/generate/)")
    gen_payload = {
        "simulation_id": simulation_id
    }
    status_code, study_plan = make_request(f"{BASE_URL}/study-plans/generate/", method="POST", data=gen_payload)
    print(f"POST /study-plans/generate/ -> Status: {status_code}")
    print(json.dumps(study_plan, indent=2, ensure_ascii=False))

    plan_items = study_plan.get("plan_semanal", [])
    if not plan_items:
        print("Error: No se generaron ítems de plan de estudio")
        sys.exit(1)

    # 6. Test POST /study-plans/{id}/feedback/
    print_section("6. Test de Registrar Feedback del Estudiante (/study-plans/{id}/feedback/)")
    first_item_id = plan_items[0]["id"]
    feedback_payload = {
        "cumplido": True,
        "horas_reales_estudiadas": 2.5,
        "resultado_obtenido": "Completé la guía de ejercicios prácticos de Análisis Matemático"
    }
    status_code, feedback_res = make_request(
        f"{BASE_URL}/study-plans/{first_item_id}/feedback/",
        method="POST",
        data=feedback_payload
    )
    print(f"POST /study-plans/{first_item_id}/feedback/ -> Status: {status_code}")
    print(json.dumps(feedback_res, indent=2, ensure_ascii=False))

    print_section("Pruebas E2E Finalizadas con Éxito")


if __name__ == "__main__":
    main()
