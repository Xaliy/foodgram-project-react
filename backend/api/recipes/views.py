from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.permissions import IsAdminAuthorOrReadOnly
from recipes.models import (Tag, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Favorite)
from .filters import CustomFilterIngredient, CustomFilterRecipe
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeSerializer, RecipePostSerializer,
                          FavoriteRecipeSerializer,
                          ShoppingCartSerializer)


User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Представление список ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = IsAdminAuthorOrReadOnly
    filterset_class = CustomFilterIngredient
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    Представление класса Recipe.
    Методы: выбор класса сериализатора,
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminAuthorOrReadOnly)
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = CustomFilterRecipe

    def get_serializer_class(self):
        """Метод для выбора класса сериализатора."""
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipePostSerializer

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """
        Метод обрабатывает запросы по формированию корзины.
        Если POST, то рецепт добавляется в корзину.
        Если DELETE, то рецепт удаляет из корзины.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id,
                'recipe': recipe.id}
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
        )

        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)

        if ShoppingCart.objects.filter(user=data['user'],
                                       recipe=data['recipe']
                                       ).exists():
            ShoppingCart.objects.get(user=data['user'],
                                     recipe=data['recipe']
                                     ).delete()
            return Response({'status': 'Рецепт удален из корзины'},
                            status=HTTPStatus.OK,)

        return Response({'status': 'Рецепта в корзине нет'},
                        status=HTTPStatus.BAD_REQUEST,)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
    )
    def favorite(self, request, pk):
        """
        Метод обрабатывает запросы на формирование списка избранных рецептов.
        Если POST, то рецепт добавляется в список.
        Если DELETE, то удаляет рецепт из списка.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        data = {
            'user': user.id,
            'recipe': recipe.id
        }
        serializer = FavoriteRecipeSerializer(data=data,
                                              context={'request': request})

        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)

        if Favorite.objects.filter(user=data['user'],
                                   recipe=data['recipe']).exists():
            Favorite.objects.get(user=data['user'],
                                 recipe=data['recipe']).delete()
            return Response({'status': 'Рецепт удален из списка избранных'},
                            status=HTTPStatus.OK,)

        return Response({'status': 'Рецепта нет в списке избранных'},
                        status=HTTPStatus.BAD_REQUEST,)

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
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__unit_of_measurement'
        ).annotate(amount=sum('amount'))
        shopping_list = 'Список покупок:'

        for ingredient in ingredients:
            shopping_list.append(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__unit_of_measurement']}) - "
                f"{ingredient['amount']}"
            )

        shopping_list = '\n'.join(shopping_list)

        file = 'shopping_list.txt'
        file_content = shopping_list.encode('utf-8')

        response = HttpResponse(file_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        response['Content-Length'] = len(file_content)

        return response
