from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Appointment, Doctor, Profile, Slot


class HospitalMsApiTests(APITestCase):
    api_prefix = '/api'

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='strong-password')
        Profile.objects.create(user=self.admin, role='admin')
        self.doctor_user = User.objects.create_user(username='doctor', password='strong-password')
        Profile.objects.create(user=self.doctor_user, role='doctor')
        self.doctor = Doctor.objects.create(user=self.doctor_user, name='Dr Grace Hopper', specialty='General')
        self.patient = User.objects.create_user(
            username='patient', email='patient@example.com', password='strong-password',
        )
        Profile.objects.create(user=self.patient, role='patient')
        self.slot = Slot.objects.create(
            doctor=self.doctor, date=timezone.localdate(), start_time='10:00',
        )

    def test_login_accepts_an_email_in_the_frontend_identifier_field(self):
        response = self.client.post(
            f'{self.api_prefix}/auth/login/',
            {'username': 'patient@example.com', 'password': 'strong-password'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_patient_can_book_an_available_slot_once(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(
            f'{self.api_prefix}/appointments/book/', {'slot_id': self.slot.id}, format='json',
        )
        duplicate = self.client.post(
            f'{self.api_prefix}/appointments/book/', {'slot_id': self.slot.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'confirmed')
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_doctor_can_record_diagnosis_and_treatment(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, slot=self.slot,
            date=self.slot.date, status='confirmed',
        )
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(
            f'{self.api_prefix}/doctor/appointments/{appointment.id}/treatment/',
            {'diagnosis': 'Seasonal allergy', 'treatment': 'Antihistamine once daily.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['diagnosis'], 'Seasonal allergy')

    def test_admin_can_update_an_appointment_status(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, slot=self.slot,
            date=self.slot.date, status='pending',
        )
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'{self.api_prefix}/admin/appointments/{appointment.id}/status/',
            {'status': 'cancelled'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')

    def test_non_admin_cannot_manage_appointments(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(f'{self.api_prefix}/admin/appointments/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
