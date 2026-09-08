from django.urls import path
from apps.assistant.views import (
    PredictSimulationAPIView,
    GenerateStudyPlanAPIView,
    StudyPlanFeedbackAPIView
)

urlpatterns = [
    path('simulations/predict/', PredictSimulationAPIView.as_view(), name='simulations-predict'),
    path('study-plans/generate/', GenerateStudyPlanAPIView.as_view(), name='study-plans-generate'),
    path('study-plans/<int:id>/feedback/', StudyPlanFeedbackAPIView.as_view(), name='study-plans-feedback'),
]
