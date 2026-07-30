import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()



@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username="testuser",
        password="testpass123"
    )
    return user


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client