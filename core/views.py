from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Appointment, Doctor, Profile, Slot
from .serializers import (
    AccountSettingsSerializer,
    AppointmentSerializer,
    BookAppointmentSerializer,
    DiagnosisSerializer,
    DoctorSerializer,
    RegisterSerializer,
    SlotSerializer,
    TreatmentSerializer,
    UpdateStatusSerializer,
)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, 'profile', None) is not None
            and request.user.profile.role == 'admin'
        )


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, 'profile', None) is not None
            and request.user.profile.role == 'doctor'
        )


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        identifier = request.data.get('email') or request.data.get('username')
        if identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                data = request.data.copy()
                data['username'] = user.username
                request._full_data = data
        return super().post(request, *args, **kwargs)


class AccountSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(AccountSettingsSerializer(request.user.profile).data)

    def patch(self, request):
        serializer = AccountSettingsSerializer(request.user.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(AccountSettingsSerializer(serializer.save()).data)


class PatientDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.filter(patient=request.user).select_related('doctor', 'slot')
        return Response({
            'upcoming': AppointmentSerializer(
                appointments.filter(status__in=['pending', 'confirmed'], date__gte=timezone.localdate()),
                many=True,
            ).data,
            'history': AppointmentSerializer(
                appointments.filter(status__in=['completed', 'cancelled']).order_by('-date', '-created_at'),
                many=True,
            ).data,
        })


class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Doctor.objects.annotate(
            available_slots=Count('slots', filter=Q(slots__is_booked=False, slots__date__gte=timezone.localdate()))
        )
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__iexact=specialty)
        return queryset.order_by('name')


class DoctorDetailView(generics.RetrieveAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Doctor.objects.annotate(
            available_slots=Count('slots', filter=Q(slots__is_booked=False, slots__date__gte=timezone.localdate()))
        )


class SlotListView(generics.ListAPIView):
    serializer_class = SlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Slot.objects.filter(is_booked=False, date__gte=timezone.localdate())
        if doctor_id := self.request.query_params.get('doctor'):
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset


class BookAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            slot = get_object_or_404(Slot.objects.select_for_update(), id=serializer.validated_data['slot_id'])
            if slot.is_booked:
                return Response({'detail': 'This slot is already booked.'}, status=status.HTTP_400_BAD_REQUEST)
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=slot.doctor,
                slot=slot,
                date=slot.date,
                status='confirmed',
            )
            slot.is_booked = True
            slot.save(update_fields=['is_booked'])
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


class DoctorScheduledAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return Appointment.objects.filter(
            doctor__user=self.request.user,
            date__gte=timezone.localdate(),
            status__in=['pending', 'confirmed'],
        ).select_related('patient', 'slot').order_by('date', 'slot__start_time')


class DoctorDashboardView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return Appointment.objects.filter(
            doctor__user=self.request.user,
            status='completed',
        ).select_related('patient', 'slot').order_by('-date', '-completed_at')


class DoctorDiagnosisView(APIView):
    permission_classes = [IsDoctor]

    def patch(self, request, appointment_id):
        serializer = DiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor__user=request.user)
        appointment.diagnosis = serializer.validated_data['diagnosis']
        appointment.save(update_fields=['diagnosis'])
        return Response(AppointmentSerializer(appointment).data)


class DoctorTreatmentView(APIView):
    permission_classes = [IsDoctor]

    def patch(self, request, appointment_id):
        serializer = TreatmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor__user=request.user,
            status__in=['pending', 'confirmed', 'completed'],
        )
        appointment.treatment = serializer.validated_data['treatment']
        if 'diagnosis' in serializer.validated_data:
            appointment.diagnosis = serializer.validated_data['diagnosis']
        appointment.status = 'completed'
        appointment.completed_at = appointment.completed_at or timezone.now()
        appointment.save(update_fields=['treatment', 'diagnosis', 'status', 'completed_at'])
        return Response(AppointmentSerializer(appointment).data)


class AdminAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = Appointment.objects.select_related('doctor', 'patient', 'slot')
        for field in ('doctor', 'status', 'date'):
            if value := self.request.query_params.get(field):
                queryset = queryset.filter(**{field: value})
        return queryset.order_by('-date', '-created_at')


class AdminUpdateStatusView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, appointment_id):
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.status = serializer.validated_data['status']
        update_fields = ['status']
        if appointment.status == 'completed':
            appointment.completed_at = appointment.completed_at or timezone.now()
            update_fields.append('completed_at')
        appointment.save(update_fields=update_fields)
        return Response(AppointmentSerializer(appointment).data)
