"""
Shared fixtures for quiz_management_app tests.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from quiz_management_app.api.views import CreateQuizView


@pytest.fixture
def api_client():
    """
    Fixture that provides an API client for making test requests.
    """
    return APIClient()


@pytest.fixture
def test_user():
    """
    Fixture that creates a test user for authenticated requests.
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """
    Fixture that provides an authenticated API client.
    """
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def view_instance():
    """
    Fixture that provides a CreateQuizView instance.
    """
    return CreateQuizView()
