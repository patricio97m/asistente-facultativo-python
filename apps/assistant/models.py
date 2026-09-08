from django.db import models
from apps.academic.models import StudentProfile, Subject


class EnrollmentSimulation(models.Model):
    NIVEL_RIESGO_CHOICES = [
        ('Bajo', 'Bajo'),
        ('Equilibrado', 'Equilibrado'),
        ('Alto', 'Alto (Alto Riesgo)'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True,
        blank=True
    )
    materias = models.ManyToManyField(
        Subject,
        related_name='simulations',
        help_text="Materias seleccionadas para la simulación del cuatrimestre"
    )
    probabilidad_promocion_calculada = models.JSONField(
        default=dict,
        help_text="Estadísticas de probabilidad calculada por materia"
    )
    horas_estudio_sugeridas_dia = models.FloatField(
        default=0.0,
        help_text="Total de horas recomendadas de estudio diario"
    )
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=NIVEL_RIESGO_CHOICES,
        default='Equilibrado',
        help_text="Nivel de riesgo estimado de sobrecarga/desaprobación"
    )
    alerta_sobrecarga = models.BooleanField(
        default=False,
        help_text="Indica si la suma semanal de horas excede las 168h del reloj"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Simulación de Inscripción"
        verbose_name_plural = "Simulaciones de Inscripción"
        ordering = ['-created_at']

    def __str__(self):
        return f"Simulación #{self.id} - Riesgo: {self.nivel_riesgo} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class StudyPlanItem(models.Model):
    DIAS_SEMANA = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    simulation = models.ForeignKey(
        EnrollmentSimulation,
        on_delete=models.CASCADE,
        related_name='study_plan_items'
    )
    dia_semana = models.CharField(
        max_length=15,
        choices=DIAS_SEMANA
    )
    materia = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_items'
    )
    horas_asignadas = models.FloatField(
        default=0.0,
        help_text="Horas de estudio planificadas para este día/materia"
    )
    cumplido = models.BooleanField(
        default=False,
        help_text="Feedback del alumno: True si cumplió el tiempo de estudio"
    )
    horas_reales_estudiadas = models.FloatField(
        null=True,
        blank=True,
        help_text="Feedback del alumno: Horas reales dedicadas"
    )
    resultado_obtenido = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Feedback del alumno: Calificación o desempeño percibido"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Plan de Estudio"
        verbose_name_plural = "Items de Plan de Estudio"
        ordering = ['simulation', 'id']

    def __str__(self):
        subj_name = self.materia.nombre if self.materia else 'Estudio General'
        return f"{self.dia_semana}: {subj_name} ({self.horas_asignadas}h) - Cumplido: {self.cumplido}"
