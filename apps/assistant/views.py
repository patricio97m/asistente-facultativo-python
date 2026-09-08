from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.academic.models import StudentProfile, Subject
from apps.assistant.models import EnrollmentSimulation, StudyPlanItem
from apps.assistant.serializers import (
    PredictRequestSerializer,
    PredictResponseSerializer,
    GenerateStudyPlanRequestSerializer,
    GenerateStudyPlanResponseSerializer,
    StudyPlanItemSerializer,
    FeedbackRequestSerializer
)
from apps.ml_engine.services.ml_service import MLPredictorService


# Global Singleton / Lazy initialized instance of ML Service
ml_service = MLPredictorService()


class PredictSimulationAPIView(generics.GenericAPIView):
    serializer_class = PredictRequestSerializer

    @extend_schema(
        summary="Simular cuatrimestre y predecir rendimiento (ML LightGBM)",
        description="Recibe los IDs de las materias seleccionadas y datos de disponibilidad del alumno. Ejecuta los modelos de LightGBM para predecir probabilidades de promoción, horas de estudio recomendadas y evaluar alerta de sobrecarga.",
        request=PredictRequestSerializer,
        responses={
            200: PredictResponseSerializer,
            400: OpenApiResponse(description="Parámetros o datos de entrada inválidos")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_ids = serializer.validated_data['subject_ids']

        # Get or create StudentProfile
        if request.user.is_authenticated:
            profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        else:
            profile = StudentProfile.objects.first()
            if not profile:
                profile = StudentProfile.objects.create(
                    horas_trabajo_semanal=20.0,
                    horas_sueno_objetivo=8.0,
                    promedio_general=7.0
                )

        # Allow temporary request overrides or fallback to StudentProfile
        horas_trabajo = serializer.validated_data.get('horas_trabajo_semanal')
        if horas_trabajo is None:
            horas_trabajo = profile.horas_trabajo_semanal

        horas_sueno = serializer.validated_data.get('horas_sueno_objetivo')
        if horas_sueno is None:
            horas_sueno = profile.horas_sueno_objetivo

        promedio = serializer.validated_data.get('promedio_general')
        if promedio is None:
            promedio = profile.promedio_general

        # Fetch subjects from DB
        subjects = Subject.objects.filter(id__in=subject_ids)
        subjects_data = [
            {
                'id': s.id,
                'nombre': s.nombre,
                'codigo': s.codigo,
                'promedio_historico_promocion': s.promedio_historico_promocion,
                'horas_cursada_semanal': s.horas_cursada_semanal
            }
            for s in subjects
        ]

        # Execute ML Service predictions
        prediction_result = ml_service.predict_simulation(
            promedio_general=promedio,
            horas_trabajo_semanal=horas_trabajo,
            horas_sueno_objetivo=horas_sueno,
            subjects_data=subjects_data
        )

        # Save simulation record to database
        simulation = EnrollmentSimulation.objects.create(
            student=profile,
            probabilidad_promocion_calculada=prediction_result['materias_predicciones'],
            horas_estudio_sugeridas_dia=prediction_result['horas_estudio_sugeridas_dia'],
            nivel_riesgo=prediction_result['nivel_riesgo'],
            alerta_sobrecarga=prediction_result['alerta_sobrecarga']
        )
        simulation.materias.set(subjects)

        response_payload = {
            'simulation_id': simulation.id,
            'materias_predicciones': prediction_result['materias_predicciones'],
            'horas_estudio_sugeridas_dia': prediction_result['horas_estudio_sugeridas_dia'],
            'alerta_sobrecarga': prediction_result['alerta_sobrecarga'],
            'nivel_riesgo': prediction_result['nivel_riesgo'],
            'promedio_probabilidad_promocion': prediction_result['promedio_probabilidad_promocion'],
            'resumen_horas_semanales': prediction_result['resumen_horas_semanales']
        }

        return Response(response_payload, status=status.HTTP_200_OK)


class GenerateStudyPlanAPIView(generics.GenericAPIView):
    serializer_class = GenerateStudyPlanRequestSerializer

    @extend_schema(
        summary="Generar cronograma semanal de estudio",
        description="Genera y guarda en base de datos la distribución diaria recomendada de horas de estudio por materia basándose en los resultados de una simulación.",
        request=GenerateStudyPlanRequestSerializer,
        responses={
            201: GenerateStudyPlanResponseSerializer,
            404: OpenApiResponse(description="Simulación no encontrada")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        simulation_id = serializer.validated_data['simulation_id']
        try:
            simulation = EnrollmentSimulation.objects.get(id=simulation_id)
        except EnrollmentSimulation.DoesNotExist:
            return Response(
                {"error": f"No se encontró ninguna simulación con ID {simulation_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Clear previous items if regenerated
        simulation.study_plan_items.all().delete()

        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        materias = list(simulation.materias.all())
        preds = {p['subject_id']: p for p in simulation.probabilidad_promocion_calculada}

        created_items = []

        if not materias:
            # Create rest or general items
            for dia in dias_semana:
                item = StudyPlanItem.objects.create(
                    simulation=simulation,
                    dia_semana=dia,
                    materia=None,
                    horas_asignadas=0.0
                )
                created_items.append(item)
        else:
            # Distribute study hours day by day evenly or prioritized across days
            # Mon-Fri get 5 days of focus, Sat 1 day, Sun rest/light review
            for i, dia in enumerate(dias_semana):
                if dia == 'Domingo':
                    # Sunday: Light general review
                    item = StudyPlanItem.objects.create(
                        simulation=simulation,
                        dia_semana=dia,
                        materia=None,
                        horas_asignadas=round(max(0.5, simulation.horas_estudio_sugeridas_dia * 0.4), 1)
                    )
                    created_items.append(item)
                else:
                    # Assign a primary subject for this day based on round-robin & difficulty
                    subj = materias[i % len(materias)]
                    pred_materia = preds.get(subj.id, {})
                    hours_day = pred_materia.get('horas_estudio_sugeridas_dia_materia', 1.5)

                    item = StudyPlanItem.objects.create(
                        simulation=simulation,
                        dia_semana=dia,
                        materia=subj,
                        horas_asignadas=round(hours_day, 1)
                    )
                    created_items.append(item)

        items_serializer = StudyPlanItemSerializer(created_items, many=True)
        return Response({
            'simulation_id': simulation.id,
            'total_items_generados': len(created_items),
            'plan_semanal': items_serializer.data
        }, status=status.HTTP_201_CREATED)


class StudyPlanFeedbackAPIView(generics.GenericAPIView):
    serializer_class = FeedbackRequestSerializer

    @extend_schema(
        summary="Registrar feedback sobre el plan de estudio",
        description="Permite al estudiante confirmar las horas reales estudiadas y el resultado obtenido en un ítem específico del cronograma para realimentación de futuros modelos.",
        request=FeedbackRequestSerializer,
        responses={
            200: StudyPlanItemSerializer,
            404: OpenApiResponse(description="Ítem de plan de estudio no encontrado")
        }
    )
    def post(self, request, id, *args, **kwargs):
        try:
            plan_item = StudyPlanItem.objects.get(id=id)
        except StudyPlanItem.DoesNotExist:
            return Response(
                {"error": f"No se encontró el ítem de plan de estudio con ID {id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_item.cumplido = serializer.validated_data['cumplido']
        if 'horas_reales_estudiadas' in serializer.validated_data:
            plan_item.horas_reales_estudiadas = serializer.validated_data['horas_reales_estudiadas']
        if 'resultado_obtenido' in serializer.validated_data:
            plan_item.resultado_obtenido = serializer.validated_data['resultado_obtenido']

        plan_item.save()

        response_serializer = StudyPlanItemSerializer(plan_item)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
