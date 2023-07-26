from api.recipes.serializers import UserSubscribeSerializer
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from recipes.models import Subscription
from rest_framework import filters, generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer

User = get_user_model()


class UserListView(generics.ListAPIView):
    """Список пользователей."""

    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
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
        )
        return queryset


class UserSubscriptionView(APIView):
    """Подписки пользователя."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Метод список подписок пользоваетеля. Subscriptions."""
        queryset = Subscription.objects.filter(user=request.user)
        serializer = UserSubscribeSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request, id):
        """Метод создания подписки на других авторов. Subscribe."""
        author = get_object_or_404(User, id=id)

        if request.user.id == author.id:
            if request.user.id == author.id:
                raise ValidationError('Запрещена подписка на самого себя')

        serializer = UserSubscribeSerializer(
            Subscription.objects.create(
                user=request.user,
                author=author
            ),
            context={'request': request},
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Метод удаления подписки на других авторов. Subscribe."""
        author = get_object_or_404(User, id=id)

        subscription_db = Subscription.objects.filter(
            user=request.user,
            author=author
        )

        if subscription_db.exists():
            subscription_db.delete()

            return Response(
                {'status': f'Подписка на автора {author.username} удалена'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'errors': 'Вы не подписаны на данного автора'},
            status=status.HTTP_400_BAD_REQUEST
        )
