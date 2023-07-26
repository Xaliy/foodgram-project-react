from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerialiser
from recipes.models import Subscription
from rest_framework import serializers

User = get_user_model()


class UserSerializer(DjoserUserSerialiser):
    """Сериализатор модели User. Валидация username, email."""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'role', 'password')

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


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор создания User."""

    class Meta:
        fields = ('username', 'password', 'email',
                  'first_name', 'last_name',)
        model = User
