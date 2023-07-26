from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerialiser
from recipes.models import Subscription
from rest_framework import serializers

User = get_user_model()


class UserSerializer(DjoserUserSerialiser):
    """Сериализатор модели User создания пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed')

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
        model = User
        fields = ('username', 'password', 'email',
                  'first_name', 'last_name')

    def validate_email(self, value):
        """Метод проверки зарегистрированного Email."""
        norm_email = value.lower()
        if User.objects.filter(email=norm_email).exists():
            raise serializers.ValidationError('Email уже зарегистрирован')
        return norm_email

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError('me зарегистрировано системой')
        return value


class ReadSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя Subscription."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()
