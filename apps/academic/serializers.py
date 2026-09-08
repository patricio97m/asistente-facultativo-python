from rest_framework import serializers
from apps.academic.models import StudentProfile, Subject


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'username',
            'horas_trabajo_semanal',
            'horas_sueno_objetivo',
            'promedio_general',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_horas_trabajo_semanal(self, value):
        if value < 0 or value > 112:
            raise serializers.ValidationError("Las horas de trabajo semanal deben estar entre 0 y 112.")
        return value

    def validate_horas_sueno_objetivo(self, value):
        if value < 1 or value > 24:
            raise serializers.ValidationError("Las horas de sueño objetivo deben estar entre 1 y 24.")
        return value

    def validate_promedio_general(self, value):
        if value < 1.0 or value > 10.0:
            raise serializers.ValidationError("El promedio general debe estar entre 1.0 y 10.0.")
        return value


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            'id',
            'nombre',
            'codigo',
            'promedio_historico_promocion',
            'horas_cursada_semanal',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_promedio_historico_promocion(self, value):
        if value < 1.0 or value > 10.0:
            raise serializers.ValidationError("El promedio histórico debe estar entre 1.0 y 10.0.")
        return value

    def validate_horas_cursada_semanal(self, value):
        if value <= 0 or value > 60:
            raise serializers.ValidationError("Las horas de cursada semanal deben ser mayores a 0 y menores a 60.")
        return value
