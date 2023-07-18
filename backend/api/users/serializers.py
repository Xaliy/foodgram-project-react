from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Subscription


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели User. Валидация username, email."""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'role', 'password')

    def validate_username(self, value):
        """Метод проверки значения me зарегестрированного системой."""
        if value == 'me':
            raise serializers.ValidationError('me зарегистрировано системой')
        return value

    def validate_email(self, value):
        """Метод проверки зарегистрированного Email."""
        norm_email = value.lower()
        if User.objects.filter(email=norm_email).exists():
            raise serializers.ValidationError('Email уже зарегистрирован')
        return norm_email

    def get_is_subscribed(self, obj):
        """Метод наличия подписки на пользователя модели Subscription."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, subscription_id=obj.pk
        ).exists()


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор создания User."""

    class Meta:
        fields = ('username', 'password', 'email',
                  'first_name', 'last_name',)
        model = User

    def validate_username(self, value):
        """Метод проверки значения me зарегестрированного системой."""
        if value == 'me':
            raise serializers.ValidationError('me зарегистрировано системой')
        return value
