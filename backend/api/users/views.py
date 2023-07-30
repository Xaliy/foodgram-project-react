from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from djoser.views import UserViewSet
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.paginators import CustomPaginator
from users.models import Subscription

from api.recipes.serializers import UserSubscribeSerializer

User = get_user_model()


class UsersViewSet(UserViewSet):
    """Представление модели пользователей."""

    queryset = User.objects.all()
    pagination_class = CustomPaginator
    permission_classes = (AllowAny, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        """Метод создания подписки на других авторов."""
        author = get_object_or_404(User, id=id)
        user = request.user
        subscription = Subscription.objects.filter(
            user=user, author=author
        )
        if request.method == 'DELETE':
            try:
                subscription.delete()
                return Response(
                    f'Подписка на автора {author.username} удалена',
                    status=HTTPStatus.OK)
            except ObjectDoesNotExist:
                return Response('Вы не подписаны на данного автора',
                                status=HTTPStatus.BAD_REQUEST)
        if request.user.id == author.id:
            raise ValidationError('Запрещена подписка на самого себя')
        if subscription.exists():
            raise ValidationError('Вы уже подписаны на этого автора')
        subscription = Subscription.objects.create(
            user=request.user,
            author=author
        )
        serializer = UserSubscribeSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPaginator
    )
    def subscriptions(self, request):
        """Метод список подписок пользоваетеля."""
        user = request.user
        queryset = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
