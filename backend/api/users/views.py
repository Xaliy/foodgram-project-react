from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import Subscription
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# from .serializers import ( # ReadSubscriptionsSerializer,
#                           WriteSubscriptionSerializer,
#                           UserSerializer
# )
from .serializers import (WriteSubscriptionSerializer,
                          UserSerializer)

User = get_user_model()


class SubscribeView(APIView):
    """Подписка на авторов."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        """Метод создания подписки на других авторов. Subscribe."""
        data = {
            'user': request.user.id,
            'author': id
        }
        serializer = WriteSubscriptionSerializer(
            data=data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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


class SubscriptionsView(ListAPIView):
    """Список подписок пользователя. Subscriptions."""

    permission_classes = [IsAuthenticated]
    serializer_class = WriteSubscriptionSerializer

    def get_queryset(self):
        """Метод список подписок пользоваетеля. Subscriptions."""
        return Subscription.objects.filter(user=self.request.user)

    def get_subscriptions(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
