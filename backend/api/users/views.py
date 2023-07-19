from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from djoser.views import UserViewSet
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAdmin
from api.recipes.serializers import UserSubscribeSerializer
from recipes.models import Subscription

from .serializers import UserSerializer

User = get_user_model()


class UsersViewSet(UserViewSet):
    """Представление модели пользователей."""

    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    lookup_field = 'username'
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    def get_queryset(self):
        """
        Метод используется для получения списка пользователей
        в ответе на запрос. Приобразовываем базовый get_queryset()
        и добавляем флаг is_subscribed для каждого пользователя.
        """
        queryset = User.objects.annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(
                    user=self.request.user,
                    author=OuterRef('id')
                )
            )
        ).all()
        return queryset

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def create_subscription(self, request, id):
        """Метод создания подписки на других авторов."""
        author = get_object_or_404(User, id=id)

        if request.user.id == author.id:
            raise ValidationError('Запрещена подписка на самого себя')

        serializer = UserSubscribeSerializer(
            Subscription.objects.create(
                user=request.user,
                author=author
            ),
            context={'request': request},
        )

        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=['DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def delete_subscription(self, request, id):
        """Метод удаления подписки на других авторов."""
        author = get_object_or_404(User, id=id)

        if Subscription.objects.filter(user=request.user,
                                       author=author).exists():
            Subscription.objects.filter(user=request.user,
                                        author=author).delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response(
                {'errors': 'Вы не подписаны на данного автора'},
                status=HTTPStatus.BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Метод список подписок пользоваетеля."""
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
