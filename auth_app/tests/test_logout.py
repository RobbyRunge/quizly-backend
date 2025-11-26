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
    Fixture that creates a test user for logout tests.
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """
    Fixture that provides an authenticated API client with cookies.
    """
    login_data = {
        'username': 'testuser',
        'password': 'TestPass123'
    }
    response = api_client.post('/api/login/', login_data)

    # Set cookies in the client
    api_client.cookies['access_token'] = response.cookies['access_token'].value
    api_client.cookies['refresh_token'] = response.cookies['refresh_token'].value

    return api_client


@pytest.mark.django_db
class TestLogoutView:
    """
    Test suite for the /api/logout/ endpoint.

    Tests cover:
    - Successful logout with authentication (200)
    - Failed logout without authentication (401)
    - Cookie deletion behavior
    """

    url = '/api/logout/'

    # ===== SUCCESS CASES (200) =====

    def test_logout_success_with_authentication(
        self, authenticated_client
    ):
        """
        Test successful logout when user is authenticated.

        Expects:
        - Status 200 OK
        - Success message about token deletion
        - Cookies are cleared
        """
        response = authenticated_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == (
            'Log-Out successfully! All Tokens will be deleted. '
            'Refresh token is now invalid.'
        )

    def test_logout_clears_access_token_cookie(
        self, authenticated_client
    ):
        """
        Test that logout clears the access_token cookie.

        Expects:
        - access_token cookie is deleted (max-age=0 or empty value)
        """
        response = authenticated_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        # Check that the cookie is being deleted
        access_cookie = response.cookies.get('access_token')
        assert access_cookie is not None
        # Cookie deletion is indicated by max-age=0 or empty value
        assert (
            access_cookie.value == '' or
            access_cookie['max-age'] == 0
        )

    def test_logout_clears_refresh_token_cookie(
        self, authenticated_client
    ):
        """
        Test that logout clears the refresh_token cookie.

        Expects:
        - refresh_token cookie is deleted (max-age=0 or empty value)
        """
        response = authenticated_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        # Check that the cookie is being deleted
        refresh_cookie = response.cookies.get('refresh_token')
        assert refresh_cookie is not None
        # Cookie deletion is indicated by max-age=0 or empty value
        assert (
            refresh_cookie.value == '' or
            refresh_cookie['max-age'] == 0
        )

    def test_logout_clears_both_cookies(
        self, authenticated_client
    ):
        """
        Test that logout clears both access and refresh token cookies.

        Expects:
        - Both cookies are present in response (being deleted)
        """
        response = authenticated_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies

    def test_logout_multiple_times_succeeds(
        self, authenticated_client
    ):
        """
        Test that logout can be called multiple times successfully.

        Expects:
        - First logout succeeds
        - Second logout without re-authentication fails with 401
        """
        # First logout
        response1 = authenticated_client.post(self.url)
        assert response1.status_code == status.HTTP_200_OK

        # Clear cookies after logout
        authenticated_client.cookies.clear()

        # Second logout should fail (no authentication)
        response2 = authenticated_client.post(self.url)
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED

    # ===== FAILURE CASES (401) =====

    def test_logout_without_authentication(self, api_client):
        """
        Test logout fails when user is not authenticated.

        Expects:
        - Status 401 Unauthorized
        - Error message about missing credentials
        """
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data

    def test_logout_with_invalid_token(self, api_client):
        """
        Test logout fails with invalid access token.

        Expects:
        - Status 401 Unauthorized
        - Error message about invalid token
        """
        # Set invalid token in cookies
        api_client.cookies['access_token'] = 'invalid_token_string'

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_with_empty_token(self, api_client):
        """
        Test logout fails with empty access token.

        Expects:
        - Status 401 Unauthorized
        """
        api_client.cookies['access_token'] = ''

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_with_only_refresh_token(
        self, api_client, test_user
    ):
        """
        Test logout fails when only refresh token is provided.

        Expects:
        - Status 401 Unauthorized (access token required)
        """
        # Login to get tokens
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        login_response = api_client.post('/api/login/', login_data)

        # Clear all cookies first
        api_client.cookies.clear()

        # Set only refresh token (not access token)
        api_client.cookies['refresh_token'] = (
            login_response.cookies['refresh_token'].value
        )

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_with_expired_token(self, api_client):
        """
        Test logout fails with expired access token.

        Expects:
        - Status 401 Unauthorized
        - Error about token expiration
        """
        # Use a token that is clearly expired/malformed
        expired_token = (
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.'
            'eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwfQ.'
            'invalid_signature'
        )
        api_client.cookies['access_token'] = expired_token

        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ===== EDGE CASES =====

    def test_logout_with_empty_body(self, authenticated_client):
        """
        Test logout works with empty request body.

        Expects:
        - Status 200 OK (body not required)
        """
        response = authenticated_client.post(self.url, {})

        assert response.status_code == status.HTTP_200_OK

    def test_logout_with_extra_data_in_body(
        self, authenticated_client
    ):
        """
        Test logout ignores extra data in request body.

        Expects:
        - Status 200 OK (extra data is ignored)
        """
        data = {
            'extra_field': 'some_value',
            'another_field': 123
        }
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_logout_response_message_format(
        self, authenticated_client
    ):
        """
        Test that logout response has correct message format.

        Expects:
        - Response contains 'detail' key
        - Message mentions token deletion and invalidation
        """
        response = authenticated_client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        detail_message = response.data['detail'].lower()
        assert 'log-out' in detail_message or 'logout' in detail_message
        assert 'token' in detail_message
        assert 'invalid' in detail_message
