import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


@pytest.fixture
def api_client():
    """
    Fixture that provides an API client for making test requests.
    """
    return APIClient()


@pytest.fixture
def valid_user_data():
    """
    Fixture providing valid user registration data.
    """
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123',
        'confirmed_password': 'SecurePass123'
    }


@pytest.fixture
def existing_user():
    """
    Fixture that creates an existing user for testing duplicates.
    """
    return User.objects.create_user(
        username='existinguser',
        email='existing@example.com',
        password='ExistingPass123'
    )


@pytest.mark.django_db
class TestRegisterView:
    """
    Test suite for the /api/register/ endpoint.

    Tests cover:
    - Successful user registration (201)
    - Invalid data validation (400)
    - Edge cases and error scenarios
    """

    url = '/api/register/'

    # ===== SUCCESS CASES (201) =====

    def test_register_user_success(self, api_client, valid_user_data):
        """
        Test successful user registration with valid data.

        Expects:
        - Status 201 Created
        - Success message in response
        - User created in database
        """
        response = api_client.post(self.url, valid_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['detail'] == 'User created successfully!'
        assert User.objects.filter(username='testuser').exists()

    def test_register_user_password_is_hashed(self, api_client, valid_user_data):
        """
        Test that password is properly hashed (not stored as plaintext).

        Expects:
        - Password is hashed using Django's password hashing
        - Can authenticate with original password
        """
        api_client.post(self.url, valid_user_data)
        user = User.objects.get(username='testuser')

        # Password should not be stored as plaintext
        assert user.password != 'SecurePass123'
        # Should be able to authenticate with correct password
        assert user.check_password('SecurePass123')

    def test_register_user_with_special_chars_in_email(self, api_client):
        """
        Test registration with special characters in email.

        Expects:
        - Accepts valid email formats with dots, plus signs, etc.
        """
        data = {
            'username': 'specialuser',
            'email': 'test.user+tag@example.co.uk',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED

    # ===== VALIDATION ERRORS (400) =====

    def test_register_user_passwords_do_not_match(self, api_client):
        """
        Test registration fails when passwords don't match.

        Expects:
        - Status 400 Bad Request
        - Error message about password mismatch
        """
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'DifferentPass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirmed_password' in response.data

    # Password length validation removed in new implementation

    # Username length validation removed in new implementation

    # Duplicate username check removed in new implementation

    def test_register_user_duplicate_email(self, api_client, existing_user):
        """
        Test registration fails with already existing email.

        Expects:
        - Status 400 Bad Request
        - Error message about duplicate email
        """
        data = {
            'username': 'newusername',
            'email': 'existing@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_missing_username(self, api_client):
        """
        Test registration fails when username is missing.

        Expects:
        - Status 400 Bad Request
        - Error message about required username
        """
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_register_user_missing_email(self, api_client):
        """
        Test registration fails when email is missing.

        Expects:
        - Status 400 Bad Request
        - Error message about required email
        """
        data = {
            'username': 'testuser',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_missing_password(self, api_client):
        """
        Test registration fails when password is missing.

        Expects:
        - Status 400 Bad Request
        - Error message about required password
        """
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_missing_confirmed_password(self, api_client):
        """
        Test registration fails when confirmed_password is missing.

        Expects:
        - Status 400 Bad Request
        - Error message about required confirmed_password
        """
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirmed_password' in response.data

    def test_register_user_invalid_email_format(self, api_client):
        """
        Test registration fails with invalid email format.

        Expects:
        - Status 400 Bad Request
        - Error message about invalid email
        """
        data = {
            'username': 'testuser',
            'email': 'invalid-email-format',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_empty_fields(self, api_client):
        """
        Test registration fails with empty string fields.

        Expects:
        - Status 400 Bad Request
        - Multiple validation errors
        """
        data = {
            'username': '',
            'email': '',
            'password': '',
            'confirmed_password': ''
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'password' in response.data
        assert 'confirmed_password' in response.data

    def test_register_user_no_data(self, api_client):
        """
        Test registration fails when no data is provided.

        Expects:
        - Status 400 Bad Request
        - Errors for all required fields
        """
        response = api_client.post(self.url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'email' in response.data
        assert 'password' in response.data

    # ===== EDGE CASES =====

    def test_register_user_username_with_numbers(self, api_client):
        """
        Test successful registration with numbers in username.

        Expects:
        - Status 201 Created
        - Accepts alphanumeric usernames
        """
        data = {
            'username': 'user123',
            'email': 'user123@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_register_user_case_sensitive_username(self, api_client, existing_user):
        """
        Test that username comparison is case-sensitive.

        Expects:
        - 'ExistingUser' is different from 'existinguser'
        - Can create user with different case
        """
        data = {
            'username': 'ExistingUser',
            'email': 'different@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        # Django default behavior: usernames are case-sensitive
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_user_whitespace_trimming(self, api_client):
        """
        Test that leading/trailing whitespace is trimmed by DRF.

        Expects:
        - Django REST Framework trims whitespace by default
        - User is created successfully with trimmed values
        """
        data = {
            'username': '  testuser  ',
            'email': '  test@example.com  ',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        # DRF automatically trims whitespace
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email='test@example.com')
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'

    def test_register_user_sql_injection_attempt(self, api_client):
        """
        Test security: SQL injection attempts are handled safely.

        Expects:
        - No SQL injection vulnerability
        - Either creates user with special chars or rejects input
        """
        data = {
            'username': "admin'--",
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'confirmed_password': 'SecurePass123'
        }
        response = api_client.post(self.url, data)

        # Should either succeed or fail gracefully (not cause SQL error)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_register_multiple_users_sequentially(self, api_client):
        """
        Test that multiple users can be created one after another.

        Expects:
        - Each user is created independently
        - No conflicts between sequential registrations
        """
        users = [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': 'SecurePass123',
                'confirmed_password': 'SecurePass123'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'password': 'SecurePass123',
                'confirmed_password': 'SecurePass123'
            },
            {
                'username': 'user3',
                'email': 'user3@example.com',
                'password': 'SecurePass123',
                'confirmed_password': 'SecurePass123'
            }
        ]

        for user_data in users:
            response = api_client.post(self.url, user_data)
            assert response.status_code == status.HTTP_201_CREATED

        assert User.objects.count() == 3
