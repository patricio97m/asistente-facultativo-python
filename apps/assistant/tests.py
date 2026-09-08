from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.academic.models import Subject, StudentProfile
from apps.assistant.models import EnrollmentSimulation, StudyPlanItem


class AsistenteFacultativoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create student profile
        self.profile = StudentProfile.objects.create(
            horas_trabajo_semanal=20.0,
            horas_sueno_objetivo=7.0,
            promedio_general=7.5
        )

        # Create sample subjects
        self.subject1 = Subject.objects.create(
            codigo='MAT-101',
            nombre='Análisis Matemático I',
            promedio_historico_promocion=6.0,
            horas_cursada_semanal=6.0
        )
        self.subject2 = Subject.objects.create(
            codigo='INF-101',
            nombre='Programación Básica',
            promedio_historico_promocion=7.5,
            horas_cursada_semanal=6.0
        )

    def test_student_profile_endpoint(self):
        url = reverse('student-profile')

        # GET Profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['promedio_general'], 7.5)

        # POST Profile update
        update_data = {
            'horas_trabajo_semanal': 25.0,
            'horas_sueno_objetivo': 8.0,
            'promedio_general': 8.0
        }
        response = self.client.post(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['horas_trabajo_semanal'], 25.0)

    def test_subject_list_endpoint(self):
        url = reverse('subject-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_predict_simulation_endpoint(self):
        url = reverse('simulations-predict')
        payload = {
            'subject_ids': [self.subject1.id, self.subject2.id],
            'horas_trabajo_semanal': 20.0,
            'horas_sueno_objetivo': 7.0,
            'promedio_general': 7.5
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('simulation_id', response.data)
        self.assertIn('materias_predicciones', response.data)
        self.assertIn('alerta_sobrecarga', response.data)
        self.assertIn('nivel_riesgo', response.data)

        simulation_id = response.data['simulation_id']
        self.assertTrue(EnrollmentSimulation.objects.filter(id=simulation_id).exists())

    def test_generate_study_plan_endpoint(self):
        # First predict simulation
        url_predict = reverse('simulations-predict')
        payload_predict = {
            'subject_ids': [self.subject1.id, self.subject2.id]
        }
        resp_pred = self.client.post(url_predict, payload_predict, format='json')
        sim_id = resp_pred.data['simulation_id']

        # Generate study plan
        url_gen = reverse('study-plans-generate')
        payload_gen = {'simulation_id': sim_id}
        response = self.client.post(url_gen, payload_gen, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['simulation_id'], sim_id)
        self.assertEqual(response.data['total_items_generados'], 7)

    def test_study_plan_feedback_endpoint(self):
        # Create simulation & item
        sim = EnrollmentSimulation.objects.create(
            student=self.profile,
            horas_estudio_sugeridas_dia=2.0,
            nivel_riesgo='Bajo'
        )
        item = StudyPlanItem.objects.create(
            simulation=sim,
            dia_semana='Lunes',
            materia=self.subject1,
            horas_asignadas=2.0
        )

        url_fb = reverse('study-plans-feedback', kwargs={'id': item.id})
        fb_payload = {
            'cumplido': True,
            'horas_reales_estudiadas': 2.5,
            'resultado_obtenido': 'Aprobé el parcial con 8'
        }

        response = self.client.post(url_fb, fb_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['cumplido'])
        self.assertEqual(response.data['horas_reales_estudiadas'], 2.5)
