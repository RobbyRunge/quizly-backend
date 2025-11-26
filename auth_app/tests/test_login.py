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
def test_user():
    """
    Fixture that creates a test user for login tests.
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123'
    )


@pytest.mark.django_db
class TestCookieTokenObtainPairView:
    """
    Test suite for the /api/login/ endpoint (login with cookies).

    Tests cover:
    - Successful login with username and password
    - Failed login attempts
    - Cookie setting behavior
    """

    url = '/api/login/'

    # ===== SUCCESS CASES (200) =====

    def test_login_success_with_username(self, api_client, test_user):
        """
        Test successful login with username and password.

        Expects:
        - Status 200 OK
        - Success message with user data
        - access_token and refresh_token cookies set
        """
        data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Login successfully!'
        assert 'user' in response.data
        assert response.data['user']['username'] == 'testuser'
        assert response.data['user']['email'] == 'test@example.com'
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies

    def test_login_cookies_are_httponly(self, api_client, test_user):
        """
        Test that cookies are set with HttpOnly flag for security.

        Expects:
        - Both cookies have httponly=True
        - Both cookies have secure=True
        - Both cookies have samesite='Lax'
        """
        data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        response = api_client.post(self.url, data)

        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']

        assert access_cookie['httponly'] is True
        assert access_cookie['secure'] is True
        assert access_cookie['samesite'] == 'Lax'

        assert refresh_cookie['httponly'] is True
        assert refresh_cookie['secure'] is True
        assert refresh_cookie['samesite'] == 'Lax'

    # ===== FAILURE CASES (400) =====

    def test_login_with_wrong_password(self, api_client, test_user):
        """
        Test login fails with incorrect password.

        Expects:
        - Status 401 Unauthorized
        - Error message
        """
        data = {
            'username': 'testuser',
            'password': 'WrongPassword123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == 'Invalid credentials.'

    def test_login_with_nonexistent_username(self, api_client):
        """
        Test login fails with username that doesn't exist.

        Expects:
        - Status 401 Unauthorized
        - Error message
        """
        data = {
            'username': 'nonexistent',
            'password': 'TestPass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_username(self, api_client):
        """
        Test login fails when username is missing.

        Expects:
        - Status 400 Bad Request
        """
        data = {
            'password': 'TestPass123'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_password(self, api_client):
        """
        Test login fails when password is missing.

        Expects:
        - Status 400 Bad Request
        """
        data = {
            'username': 'testuser'
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_empty_credentials(self, api_client):
        """
        Test login fails with empty username and password.

        Expects:
        - Status 400 Bad Request
        """
        data = {
            'username': '',
            'password': ''
        }
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Email format validation removed (using username now)


@pytest.mark.django_db
class TestCookieTokenRefreshView:
    """
    Test suite for the /api/token/refresh/ endpoint.

    Tests cover:
    - Successful token refresh with valid refresh token
    - Failed refresh attempts
    """

    url = '/api/token/refresh/'
    login_url = '/api/login/'

    # ===== SUCCESS CASES (200) =====

    def test_refresh_token_success(self, api_client, test_user):
        """
        Test successful token refresh with valid refresh token in cookie.

        Expects:
        - Status 200 OK
        - Success message
        - New access_token cookie set
        """
        # First login to get refresh token
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        login_response = api_client.post(self.login_url, login_data)
        refresh_token = login_response.cookies['refresh_token'].value

        # Set the refresh token cookie for the refresh request
        api_client.cookies['refresh_token'] = refresh_token

        # Now refresh the token
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Token refreshed.'
        assert 'access_token' in response.cookies

    def test_refresh_token_updates_access_token(self, api_client, test_user):
        """
        Test that refresh generates a new access token.

        Expects:
        - New access token is different from old one
        """
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        login_response = api_client.post(self.login_url, login_data)
        old_access_token = login_response.cookies['access_token'].value
        refresh_token = login_response.cookies['refresh_token'].value

        # Refresh
        api_client.cookies['refresh_token'] = refresh_token
        refresh_response = api_client.post(self.url)
        new_access_token = refresh_response.cookies['access_token'].value

        # Access token should be different
        assert new_access_token != old_access_token

    # ===== FAILURE CASES (400) =====

    def test_refresh_token_missing_cookie(self, api_client):
        """
        Test refresh fails when refresh token cookie is missing.

        Expects:
        - Status 401 Unauthorized
        - Error message about missing refresh token
        """
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
        assert 'not found' in response.data['error'].lower()

    def test_refresh_token_invalid_token(self, api_client):
        """
        Test refresh fails with invalid refresh token.

        Expects:
        - Status 401 Unauthorized
        - Error message about invalid token
        """
        # Set an invalid refresh token
        api_client.cookies['refresh_token'] = 'invalid_token_string'

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
        assert 'invalid' in response.data['error'].lower()

    def test_refresh_token_empty_cookie(self, api_client):
        """
        Test refresh fails with empty refresh token cookie.

        Expects:
        - Status 401 Unauthorized
        """
        api_client.cookies['refresh_token'] = ''

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
