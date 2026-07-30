from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AccountSettingsView,
    AdminAppointmentListView,
    AdminUpdateStatusView,
    BookAppointmentView,
    DoctorDashboardView,
    DoctorDetailView,
    DoctorDiagnosisView,
    DoctorListView,
    DoctorScheduledAppointmentsView,
    DoctorTreatmentView,
    EmailTokenObtainPairView,
    PatientDashboardView,
    RegisterView,
    SlotListView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', EmailTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/settings/', AccountSettingsView.as_view(), name='account-settings'),
    path('dashboard/patient/', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('slots/', SlotListView.as_view(), name='slot-list'),
    path('appointments/book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('doctor/appointments/', DoctorScheduledAppointmentsView.as_view(), name='doctor-appointments'),
    path('doctor/dashboard/', DoctorDashboardView.as_view(), name='doctor-dashboard'),
    path('doctor/appointments/<int:appointment_id>/diagnosis/', DoctorDiagnosisView.as_view(), name='doctor-diagnosis'),
    path('doctor/appointments/<int:appointment_id>/treatment/', DoctorTreatmentView.as_view(), name='doctor-treatment'),
    path('admin/appointments/', AdminAppointmentListView.as_view(), name='admin-appointments'),
    path('admin/appointments/<int:appointment_id>/status/', AdminUpdateStatusView.as_view(), name='admin-appointment-status'),
]
