from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        null=True,
        blank=True,
        help_text="Usuario asociado al perfil del estudiante."
    )
    horas_trabajo_semanal = models.FloatField(
        default=0.0,
        help_text="Cantidad de horas semanales dedicadas al trabajo u otras obligaciones."
    )
    horas_sueno_objetivo = models.FloatField(
        default=8.0,
        help_text="Horas de sueño diarias deseadas/objetivo."
    )
    promedio_general = models.FloatField(
        default=7.0,
        help_text="Promedio académico general del estudiante (1.00 a 10.00)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Estudiante"
        verbose_name_plural = "Perfiles de Estudiantes"

    def __str__(self):
        username = self.user.username if self.user else f"Estudiante #{self.id}"
        return f"{username} - Promedio: {self.promedio_general}"


class Subject(models.Model):
    nombre = models.CharField(max_length=150, help_text="Nombre de la materia")
    codigo = models.CharField(max_length=20, unique=True, help_text="Código único de la materia (ej: MAT-101)")
    promedio_historico_promocion = models.FloatField(
        default=6.5,
        help_text="Promedio histórico de notas con el cual se promociona la materia (1.0 a 10.0)"
    )
    horas_cursada_semanal = models.FloatField(
        default=4.0,
        help_text="Horas semanales de cursada presencial/virtual"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ['codigo']

    def __str__(self):
        return f"[{self.codigo}] {self.nombre} ({self.horas_cursada_semanal}h/sem)"
