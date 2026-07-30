import pytest
from datetime import date, time
from django.contrib.auth.models import User
from django.db import IntegrityError
from core.models import Doctor, Profile, Slot, Appointment


@pytest.mark.django_db
def test_create_doctor():
    doctor = Doctor.objects.create(
        name="Dr. Jane Smith",
        specialty="Cardiology"
    )

    assert doctor.name == "Dr. Jane Smith"
    assert doctor.specialty == "Cardiology"
    assert doctor.id is not None


@pytest.mark.django_db
def test_create_profile():
    user = User.objects.create_user(
        username="janedoe",
        password="testpass123"
    )

    profile = Profile.objects.create(
        user=user,
        role="patient",
        phone="0712345678"
    )

    assert profile.user.username == "janedoe"
    assert profile.role == "patient"
    assert profile.phone == "0712345678"


@pytest.mark.django_db
def test_create_slot():
    doctor = Doctor.objects.create(
        name="Dr. John Otieno",
        specialty="Dermatology"
    )

    slot = Slot.objects.create(
        doctor=doctor,
        date=date(2026, 8, 15),
        start_time=time(10, 0)
    )

    assert slot.doctor.name == "Dr. John Otieno"
    assert slot.date == date(2026, 8, 15)
    assert slot.is_booked is False


@pytest.mark.django_db
def test_cannot_create_duplicate_slot():
    doctor = Doctor.objects.create(
        name="Dr. John Otieno",
        specialty="Dermatology"
    )

    Slot.objects.create(
        doctor=doctor,
        date=date(2026, 8, 15),
        start_time=time(10, 0)
    )

    with pytest.raises(IntegrityError):
        Slot.objects.create(
            doctor=doctor,
            date=date(2026, 8, 15),
            start_time=time(10, 0)
        )


@pytest.mark.django_db
def test_create_appointment():
    patient_user = User.objects.create_user(
        username="patientjohn",
        password="testpass123"
    )

    doctor = Doctor.objects.create(
        name="Dr. Amina Yusuf",
        specialty="Pediatrics"
    )

    slot = Slot.objects.create(
        doctor=doctor,
        date=date(2026, 8, 20),
        start_time=time(9, 0)
    )

    appointment = Appointment.objects.create(
        patient=patient_user,
        doctor=doctor,
        slot=slot,
        date=date(2026, 8, 20)
    )

    assert appointment.patient.username == "patientjohn"
    assert appointment.doctor.name == "Dr. Amina Yusuf"
    assert appointment.status == "pending"