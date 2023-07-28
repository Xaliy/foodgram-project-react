from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerialiser
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Subscription

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
            user=request.user, author=obj
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


class ReadSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя Subscription."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class WriteSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки  используем в SubscribeView."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ReadSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
