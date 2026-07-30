import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status


@pytest.mark.django_db
def test_register_patient(api_client):
    url = reverse("register")
    data = {
        "email": "newpatient@example.com",
        "password": "StrongPass123!",
        "role": "patient",
        "full_name": "New Patient"
    }

    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="newpatient@example.com").exists()


@pytest.mark.django_db
def test_register_doctor_requires_doctor_name(api_client):
    url = reverse("register")
    data = {
        "email": "newdoctor@example.com",
        "password": "StrongPass123!",
        "role": "doctor"
        # doctor_name deliberately missing
    }

    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_with_email(api_client):
    User.objects.create_user(
        username="loginuser",
        email="loginuser@example.com",
        password="StrongPass123!"
    )

    url = reverse("login")
    data = {
        "email": "loginuser@example.com",
        "password": "StrongPass123!"
    }

    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data