from django.contrib import admin
from apps.academic.models import StudentProfile, Subject


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'promedio_general', 'horas_trabajo_semanal', 'horas_sueno_objetivo', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'promedio_historico_promocion', 'horas_cursada_semanal')
    search_fields = ('codigo', 'nombre')
    list_filter = ('horas_cursada_semanal',)
