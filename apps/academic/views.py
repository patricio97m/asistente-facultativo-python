from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.academic.models import StudentProfile, Subject
from apps.academic.serializers import StudentProfileSerializer, SubjectSerializer


class StudentProfileAPIView(generics.GenericAPIView):
    serializer_class = StudentProfileSerializer

    def get_queryset(self):
        return StudentProfile.objects.all()

    def get_object(self):
        """Returns student profile if authenticated or default single profile."""
        if self.request.user.is_authenticated:
            profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
            return profile

        # Fallback for unauthenticated API prototyping: use first profile or create default
        profile = StudentProfile.objects.first()
        if not profile:
            profile = StudentProfile.objects.create(
                horas_trabajo_semanal=20.0,
                horas_sueno_objetivo=7.5,
                promedio_general=7.50
            )
        return profile

    @extend_schema(
        summary="Obtener perfil del estudiante",
        description="Devuelve el perfil académico y disponibilidad horaria del estudiante.",
        responses={200: StudentProfileSerializer}
    )
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Crear o actualizar perfil del estudiante",
        description="Crea o actualiza la disponibilidad horaria, horas de sueño y promedio general.",
        request=StudentProfileSerializer,
        responses={
            200: StudentProfileSerializer,
            201: StudentProfileSerializer,
            400: OpenApiResponse(description="Error de validación en los datos enviados")
        }
    )
    def post(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectListCreateAPIView(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    @extend_schema(
        summary="Listar materias disponibles",
        description="Devuelve la lista de materias académicas con promedios históricos de promoción y horas de cursada.",
        responses={200: SubjectSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar nueva materia",
        description="Permite dar de alta una nueva materia en la base de datos.",
        request=SubjectSerializer,
        responses={201: SubjectSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
