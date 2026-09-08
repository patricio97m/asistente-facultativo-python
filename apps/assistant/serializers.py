from rest_framework import serializers
from apps.academic.models import Subject
from apps.assistant.models import EnrollmentSimulation, StudyPlanItem


class PredictRequestSerializer(serializers.Serializer):
    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista de IDs de las materias a cursar en el cuatrimestre"
    )
    horas_trabajo_semanal = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Horas semanales de trabajo (Opcional, sobreescribe el perfil)"
    )
    horas_sueno_objetivo = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Horas diarias de sueño objetivo (Opcional, sobreescribe el perfil)"
    )
    promedio_general = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Promedio general del alumno (Opcional, sobreescribe el perfil)"
    )

    def validate_subject_ids(self, value):
        existing_count = Subject.objects.filter(id__in=value).count()
        if existing_count != len(set(value)):
            raise serializers.ValidationError("Uno o más IDs de materias no existen en la base de datos.")
        return value


class SubjectPredictionDetailSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    nombre = serializers.CharField()
    codigo = serializers.CharField()
    probabilidad_promocion = serializers.FloatField()
    porcentaje_promocion = serializers.CharField()
    horas_estudio_sugeridas_dia_materia = serializers.FloatField()


class ResumenHorasSemanalesSerializer(serializers.Serializer):
    horas_cursada = serializers.FloatField()
    horas_estudio = serializers.FloatField()
    horas_trabajo = serializers.FloatField()
    horas_sueno = serializers.FloatField()
    horas_totales_ocupadas = serializers.FloatField()
    horas_libres_disponibles = serializers.FloatField()


class PredictResponseSerializer(serializers.Serializer):
    simulation_id = serializers.IntegerField()
    materias_predicciones = SubjectPredictionDetailSerializer(many=True)
    horas_estudio_sugeridas_dia = serializers.FloatField()
    alerta_sobrecarga = serializers.BooleanField()
    nivel_riesgo = serializers.CharField()
    promedio_probabilidad_promocion = serializers.FloatField()
    resumen_horas_semanales = ResumenHorasSemanalesSerializer()


class GenerateStudyPlanRequestSerializer(serializers.Serializer):
    simulation_id = serializers.IntegerField(
        help_text="ID de la simulación previamente calculada"
    )


class StudyPlanItemSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True, default="Estudio General")
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True, default="")

    class Meta:
        model = StudyPlanItem
        fields = [
            'id',
            'simulation',
            'dia_semana',
            'materia',
            'materia_nombre',
            'materia_codigo',
            'horas_asignadas',
            'cumplido',
            'horas_reales_estudiadas',
            'resultado_obtenido',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'simulation', 'created_at', 'updated_at']


class GenerateStudyPlanResponseSerializer(serializers.Serializer):
    simulation_id = serializers.IntegerField()
    total_items_generados = serializers.IntegerField()
    plan_semanal = StudyPlanItemSerializer(many=True)


class FeedbackRequestSerializer(serializers.Serializer):
    cumplido = serializers.BooleanField(
        help_text="Indica si el estudiante cumplió la meta de estudio del ítem"
    )
    horas_reales_estudiadas = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Horas efectivas estudiadas por el alumno"
    )
    resultado_obtenido = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
        help_text="Nota, feedback o comentario del estudiante"
    )
