#!/usr/bin/env bash

set -e

echo "[Asistente Facultativo] - Inicializando proyecto..."

# 1. Levantar contenedores en segundo plano (detached mode)
echo "Buildeando y levantando contenedores (Backend: 8080 | Frontend: 3000)..."
docker compose up -d --build

# 2. Esperar a que el contenedor esté activo
echo "Esperando 5 segundos a que los servicios estén completamente inicializados..."
sleep 5

# 3. Crear migraciones de apps locales si hiciera falta
echo "Generando archivos de migración (makemigrations)..."
docker compose exec web python manage.py makemigrations academic assistant

# 4. Aplicar migraciones en SQLite
echo "Aplicando migraciones de base de datos..."
docker compose exec web python manage.py migrate

# 5. Poblar materias y perfil inicial
echo "Seeding de datos iniciales (subjects & student profile)..."
docker compose exec web python manage.py seed_data

echo ""
echo "Inicialización completada con éxito"
echo "-------------------------------------------------------"
echo "Frontend Web Dashboard: http://localhost:3000"
echo "Backend REST API:        http://localhost:8080"
echo "Swagger UI:              http://localhost:8080/api/schema/swagger-ui/"
echo "ReDoc:                   http://localhost:8080/api/schema/redoc/"
echo "-------------------------------------------------------"
echo "Para ver los logs en vivo ejecuta: ./start.sh o 'docker compose logs -f'"
