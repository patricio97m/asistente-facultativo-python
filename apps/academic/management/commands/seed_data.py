from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.academic.models import Subject, StudentProfile


class Command(BaseCommand):
    help = 'Puebla la base de datos con materias de prueba y un perfil de estudiante inicial.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Iniciando sembrado de datos (Seeding)..."))

        # Create or fetch superuser / default user
        user, created = User.objects.get_or_create(
            username='estudiante_unlam',
            defaults={
                'email': 'estudiante@unlam.edu.ar',
                'first_name': 'Juan',
                'last_name': 'Pérez'
            }
        )
        if created:
            user.set_password('unlam1234')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario creado: estudiante_unlam / unlam1234"))

        # Create or fetch Student Profile
        profile, p_created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'horas_trabajo_semanal': 25.0,
                'horas_sueno_objetivo': 7.5,
                'promedio_general': 7.8
            }
        )
        if p_created:
            self.stdout.write(self.style.SUCCESS("Perfil de estudiante inicial creado."))

        # Subjects dataset (Ingeniería en Informática / Materias comunes)
        materias_data = [
            {
                'codigo': 'INF-101',
                'nombre': 'Programación Básica',
                'promedio_historico_promocion': 7.2,
                'horas_cursada_semanal': 6.0
            },
            {
                'codigo': 'MAT-101',
                'nombre': 'Análisis Matemático I',
                'promedio_historico_promocion': 5.8,
                'horas_cursada_semanal': 6.0
            },
            {
                'codigo': 'MAT-102',
                'nombre': 'Álgebra y Geometría Analítica',
                'promedio_historico_promocion': 6.1,
                'horas_cursada_semanal': 4.0
            },
            {
                'codigo': 'INF-102',
                'nombre': 'Algoritmos y Estructuras de Datos',
                'promedio_historico_promocion': 6.8,
                'horas_cursada_semanal': 6.0
            },
            {
                'codigo': 'INF-201',
                'nombre': 'Bases de Datos I',
                'promedio_historico_promocion': 7.5,
                'horas_cursada_semanal': 4.0
            },
            {
                'codigo': 'INF-202',
                'nombre': 'Sistemas Operativos',
                'promedio_historico_promocion': 6.0,
                'horas_cursada_semanal': 6.0
            },
            {
                'codigo': 'REQ-101',
                'nombre': 'Ingeniería de Requerimientos',
                'promedio_historico_promocion': 8.1,
                'horas_cursada_semanal': 4.0
            }
        ]

        count = 0
        for data in materias_data:
            obj, subj_created = Subject.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data
            )
            if subj_created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Sebrado finalizado. Materias agregadas: {count}"))
