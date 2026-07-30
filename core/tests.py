from datetime import timedelta

from django.contrib.auth.models import User
from django.conf import settings
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

    def test_anonymous_users_cannot_access_protected_endpoints(self):
        endpoints = [
            f'{self.api_prefix}/auth/me/',
            f'{self.api_prefix}/dashboard/patient/',
            f'{self.api_prefix}/doctors/',
            f'{self.api_prefix}/slots/',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_creates_a_patient_profile(self):
        response = self.client.post(
            f'{self.api_prefix}/auth/register/',
            {
                'email': 'new.patient@example.com',
                'password': 'A-safe-password-123',
                'full_name': 'New Patient',
                'phone': '+254700000000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='new.patient@example.com')
        self.assertEqual(user.first_name, 'New Patient')
        self.assertEqual(user.profile.role, 'patient')
        self.assertEqual(user.profile.phone, '+254700000000')

    def test_public_registration_cannot_create_a_doctor(self):
        response = self.client.post(
            f'{self.api_prefix}/auth/register/',
            {
                'email': 'not.a.doctor@example.com',
                'password': 'A-safe-password-123',
                'role': 'doctor',
                'doctor_name': 'Dr Not Allowed',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='not.a.doctor@example.com').exists())

    def test_only_admin_can_create_a_doctor_account(self):
        payload = {
            'email': 'new.doctor@example.com',
            'password': 'A-safe-password-123',
            'full_name': 'Katherine Johnson',
            'phone': '+254722222222',
            'doctor_name': 'Dr Katherine Johnson',
            'specialty': 'Cardiology',
        }
        self.client.force_authenticate(self.patient)
        forbidden = self.client.post(f'{self.api_prefix}/admin/doctors/', payload, format='json')
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.api_prefix}/admin/doctors/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='new.doctor@example.com')
        self.assertEqual(user.profile.role, 'doctor')
        self.assertEqual(user.doctor_profile.name, 'Dr Katherine Johnson')
        self.assertEqual(user.doctor_profile.specialty, 'Cardiology')
        self.assertEqual(response.data['doctor']['id'], user.doctor_profile.id)

    def test_only_admin_can_delete_a_doctor_account(self):
        self.client.force_authenticate(self.patient)
        forbidden = self.client.delete(f'{self.api_prefix}/admin/doctors/{self.doctor.id}/')
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Doctor.objects.filter(id=self.doctor.id).exists())

        doctor_id, user_id = self.doctor.id, self.doctor_user.id
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f'{self.api_prefix}/admin/doctors/{doctor_id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=doctor_id).exists())
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_account_settings_update_contact_details_and_password(self):
        self.client.force_authenticate(self.patient)
        response = self.client.patch(
            f'{self.api_prefix}/auth/settings/',
            {
                'email': 'changed@example.com',
                'phone': '+254711111111',
                'current_password': 'strong-password',
                'new_password': 'An-even-stronger-password-123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.patient.profile.refresh_from_db()
        self.assertEqual(self.patient.email, 'changed@example.com')
        self.assertEqual(self.patient.profile.phone, '+254711111111')
        self.assertTrue(self.patient.check_password('An-even-stronger-password-123'))

    def test_slot_list_excludes_past_and_booked_slots(self):
        past_slot = Slot.objects.create(
            doctor=self.doctor,
            date=timezone.localdate() - timedelta(days=1),
            start_time='09:00',
        )
        booked_slot = Slot.objects.create(
            doctor=self.doctor,
            date=timezone.localdate(),
            start_time='11:00',
            is_booked=True,
        )
        self.client.force_authenticate(self.patient)

        response = self.client.get(f'{self.api_prefix}/slots/?doctor={self.doctor.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {slot['id'] for slot in response.data}
        self.assertIn(self.slot.id, returned_ids)
        self.assertNotIn(past_slot.id, returned_ids)
        self.assertNotIn(booked_slot.id, returned_ids)

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

    def test_doctor_cannot_update_another_doctors_appointment(self):
        another_doctor_user = User.objects.create_user(
            username='other-doctor', password='strong-password',
        )
        Profile.objects.create(user=another_doctor_user, role='doctor')
        another_doctor = Doctor.objects.create(
            user=another_doctor_user, name='Dr Ada Lovelace', specialty='Cardiology',
        )
        another_slot = Slot.objects.create(
            doctor=another_doctor, date=timezone.localdate(), start_time='12:00',
        )
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=another_doctor, slot=another_slot,
            date=another_slot.date, status='confirmed',
        )
        self.client.force_authenticate(self.doctor_user)

        response = self.client.patch(
            f'{self.api_prefix}/doctor/appointments/{appointment.id}/diagnosis/',
            {'diagnosis': 'Unauthorized update'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        appointment.refresh_from_db()
        self.assertEqual(appointment.diagnosis, '')

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

    def test_production_cors_is_not_open_to_every_origin(self):
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
