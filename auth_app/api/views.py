from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import CustomTokenObtainPairSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """
    User registration view.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'detail': 'User created successfully!'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Custom view to obtain JWT tokens and set them in HttpOnly cookies.
    """

    def post(self, request, *args, **kwargs):
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
        from django.contrib.auth import authenticate

        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        serializer = TokenObtainPairSerializer()
        token_data = serializer.get_token(user)
        refresh = str(token_data)
        access = str(token_data.access_token)

        # Prepare response data
        response_data = {
            'detail': 'Login successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        # Set cookies for access token
        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        # Set cookies for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom view to refresh JWT access token using HttpOnly cookies.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {"error": "Refresh token not found in cookies."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Refresh token invalid."},
                status=status.HTTP_400_BAD_REQUEST
            )

        access_token = serializer.validated_data.get('access')

        response = Response({"message": "Token refreshed successfully."})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        return response
