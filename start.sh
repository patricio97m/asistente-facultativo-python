#!/usr/bin/env bash

set -e

echo "[Asistente Facultativo] - Levantando Backend (8080) y Frontend (3000) en segundo plano..."

# Levantar contenedores en segundo plano (detached mode -d)
docker compose up -d --build

echo ""
echo "Contenedores ejecutándose en segundo plano."
echo "Frontend Web Dashboard: http://localhost:3000"
echo "Backend REST API:        http://localhost:8080"
echo "Swagger UI:              http://localhost:8080/api/schema/swagger-ui/"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs en vivo: docker compose logs -f"
echo "  - Detener servicios: docker compose down"
