from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from http import HTTPStatus
from recipes.models import Subscription
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAdmin
from api.recipes.serializers import UserSubscribeSerializer
from .serializers import CustomUserSerializer


User = get_user_model()


class UsersViewSet(UserViewSet):
    """Представление модели пользователей"""
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = CustomUserSerializer
    lookup_field = 'username'
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        """Метод cоздания и удаления подписки на других авторов"""
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if request.user.id == author.id:
                raise ValidationError('Запрещена подписка на самого себя')
            serializer = UserSubscribeSerializer(
                Subscription.objects.create(
                    user=request.user,
                    author=author
                ),
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=HTTPStatus.NO_CONTENT
            )
        elif request.method == 'DELETE':
            if Subscription.objects.filter(user=request.user,
                                           author=author).exists():
                Subscription.objects.filter(user=request.user,
                                            author=author).delete()
                status = HTTPStatus.NO_CONTENT
                return Response(status)
            return Response({'errors': 'Вы не подписаны на данного автора'},
                            status=HTTPStatus.BAD_REQUEST,)

    @action(methods=['GET'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Метод список подписок пользоваетеля"""
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
