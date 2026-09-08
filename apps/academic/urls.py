from django.urls import path
from apps.academic.views import StudentProfileAPIView, SubjectListCreateAPIView

urlpatterns = [
    path('profile/', StudentProfileAPIView.as_view(), name='student-profile'),
    path('subjects/', SubjectListCreateAPIView.as_view(), name='subject-list'),
]
