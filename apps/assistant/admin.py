from django.contrib import admin
from apps.assistant.models import EnrollmentSimulation, StudyPlanItem


class StudyPlanItemInline(admin.TabularInline):
    model = StudyPlanItem
    extra = 0


@admin.register(EnrollmentSimulation)
class EnrollmentSimulationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'horas_estudio_sugeridas_dia', 'nivel_riesgo', 'alerta_sobrecarga', 'created_at')
    list_filter = ('nivel_riesgo', 'alerta_sobrecarga', 'created_at')
    inlines = [StudyPlanItemInline]


@admin.register(StudyPlanItem)
class StudyPlanItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'simulation', 'dia_semana', 'materia', 'horas_asignadas', 'cumplido', 'horas_reales_estudiadas')
    list_filter = ('dia_semana', 'cumplido')
    search_fields = ('materia__nombre', 'materia__codigo')
