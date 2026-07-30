import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from core.models import Appointment, Doctor, Profile, Slot


@pytest.mark.django_db
def test_login_accepts_email_as_identifier(api_client):
    User.objects.create_user(
        username="patient1",
        email="patient1@example.com",
        password="strong-password"
    )

    url = reverse("login")
    response = api_client.post(url, {
        "username": "patient1@example.com",
        "password": "strong-password"
    })

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_protected_endpoint_blocks_anonymous_user(api_client):
    url = reverse("me")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_registration_creates_patient_profile(api_client):
    url = reverse("register")
    response = api_client.post(url, {
        "email": "new.patient@example.com",
        "password": "A-safe-password-123",
        "full_name": "New Patient",
        "phone": "+254700000000"
    })

    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email="new.patient@example.com")
    assert user.profile.role == "patient"


@pytest.mark.django_db
def test_patient_can_book_available_slot(api_client):
    doctor_user = User.objects.create_user(username="doc1", password="strong-password")
    doctor = Doctor.objects.create(user=doctor_user, name="Dr Grace Hopper", specialty="General")
    slot = Slot.objects.create(doctor=doctor, date=timezone.localdate(), start_time="10:00")

    patient = User.objects.create_user(username="patient2", password="strong-password")
    api_client.force_authenticate(patient)

    url = reverse("book-appointment")
    response = api_client.post(url, {"slot_id": slot.id})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "confirmed"


@pytest.mark.django_db
def test_patient_cannot_book_same_slot_twice(api_client):
    doctor_user = User.objects.create_user(username="doc2", password="strong-password")
    doctor = Doctor.objects.create(user=doctor_user, name="Dr Ada Lovelace", specialty="Cardiology")
    slot = Slot.objects.create(doctor=doctor, date=timezone.localdate(), start_time="11:00")

    patient = User.objects.create_user(username="patient3", password="strong-password")
    api_client.force_authenticate(patient)

    url = reverse("book-appointment")
    api_client.post(url, {"slot_id": slot.id})
    second_response = api_client.post(url, {"slot_id": slot.id})

    assert second_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_doctor_can_add_diagnosis_and_treatment(api_client):
    doctor_user = User.objects.create_user(username="doc3", password="strong-password")
    Profile.objects.create(user=doctor_user, role="doctor")
    doctor = Doctor.objects.create(user=doctor_user, name="Dr Amina Yusuf", specialty="Pediatrics")
    slot = Slot.objects.create(doctor=doctor, date=timezone.localdate(), start_time="09:00")

    patient = User.objects.create_user(username="patient4", password="strong-password")
    appointment = Appointment.objects.create(
        patient=patient, doctor=doctor, slot=slot,
        date=slot.date, status="confirmed"
    )

    api_client.force_authenticate(doctor_user)
    url = reverse("doctor-treatment", kwargs={"appointment_id": appointment.id})
    response = api_client.patch(url, {
        "diagnosis": "Seasonal allergy",
        "treatment": "Antihistamine once daily."
    })

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "completed"


@pytest.mark.django_db
def test_admin_can_update_appointment_status(api_client):
    admin = User.objects.create_user(username="admin1", password="strong-password")
    Profile.objects.create(user=admin, role="admin")

    doctor_user = User.objects.create_user(username="doc4", password="strong-password")
    doctor = Doctor.objects.create(user=doctor_user, name="Dr John Otieno", specialty="Dermatology")
    slot = Slot.objects.create(doctor=doctor, date=timezone.localdate(), start_time="14:00")
    patient = User.objects.create_user(username="patient5", password="strong-password")
    appointment = Appointment.objects.create(
        patient=patient, doctor=doctor, slot=slot,
        date=slot.date, status="pending"
    )

    api_client.force_authenticate(admin)
    url = reverse("admin-appointment-status", kwargs={"appointment_id": appointment.id})
    response = api_client.patch(url, {"status": "cancelled"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "cancelled"


@pytest.mark.django_db
def test_non_admin_cannot_view_admin_appointments(api_client):
    patient = User.objects.create_user(username="patient6", password="strong-password")
    api_client.force_authenticate(patient)

    url = reverse("admin-appointments")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN