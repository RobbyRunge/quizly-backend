from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
        }

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        pw = self.validated_data['password']

        account = User(
            email=self.validated_data['email'], username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to authenticate users using email and password instead of username.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Incorrect username or password.'
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                'Incorrect username or password.'
            )

        attrs['username'] = user.username
        data = super().validate(attrs)
        return data
