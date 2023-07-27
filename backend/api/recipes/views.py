from http import HTTPStatus
from tempfile import TemporaryFile

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAuthor
from .filters import RecipeFilter
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipePostSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)
from .services import get_shopping_list

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny, ]
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny, ]
    filter_backends = [SearchFilter]
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    Представление класса Recipe.
    Методы: выбор класса сериализатора,
    """

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthor,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        """Метод для выбора класса сериализатора."""
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipePostSerializer

    def get_queryset(self):
        """
        Метод используется для получения списка объектов Recipe
        из базы данных и добавления в каждый объект дополнительных
        полей is_favorited и is_in_shopping_cart.
        """
        queryset = (
            Recipe.objects
            .select_related('author')
            .prefetch_related('ingredients', 'tags')
        )
        user = self.request.user
        favorite_qs = Favorite.objects.filter(user=user,
                                              recipe=OuterRef('id'))
        shopping_cart_qs = ShoppingCart.objects.filter(user=user,
                                                       recipe=OuterRef('id'))
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(favorite_qs),
                is_in_shopping_cart=Exists(shopping_cart_qs)
            )

        return queryset

    def add_to_list(self, request, pk, serializer_class, model_class):
        """
        Метод добавляет объект в список.
        Используется в методах shopping_cart и favorite.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id,
                'recipe': recipe.id}
        serializer = serializer_class(
            data=data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=HTTPStatus.CREATED)

    def remove_from_list(self, request, pk, Model, message):
        """
        Метод удаляет рецепт из списка.
        Используется в методах remove_from_cart и remove_from_favorite.
        """

        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        Model.objects.filter(user=user,
                             recipe=recipe).delete()

        return Response({'status': message}, status=HTTPStatus.OK)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Метод добавляет рецепт в корзину."""
        return self.add_to_list(request,
                                pk,
                                ShoppingCartSerializer,
                                ShoppingCart)

    @shopping_cart.mapping.delete
    def remove_from_cart(self, request, pk):
        """Метод удаляет рецепт из корзины."""
        return self.remove_from_list(request,
                                     pk,
                                     ShoppingCart,
                                     'Рецепт удален из корзины')

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Метод добавляет рецепт в список избранных."""
        return self.add_to_list(request,
                                pk,
                                FavoriteRecipeSerializer,
                                Favorite)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk):
        """Метод удаляет рецепт из списка избранных."""
        return self.remove_from_list(request,
                                     pk,
                                     Favorite,
                                     'Рецепт удален из списка избранных')

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Метод скачивания списка покупок для всех рецептов,
        которые добавлены в список покупок пользователя.
        """
        user = request.user
        shopping_list = get_shopping_list(user)

        # создаем временный файл для загрузки
        with TemporaryFile() as file:
            file.write(shopping_list.encode())
            file.seek(0)

            response = FileResponse(file, filename='shopping_list.txt')
            response['Content-Disposition'] = '''attachment;
                                                filename="shopping_list.txt"'''
            response['Content-Length'] = file.tell()

            return response
