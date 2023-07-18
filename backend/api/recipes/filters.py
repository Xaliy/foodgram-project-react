from django_filters.rest_framework import (CharFilter, FilterSet,
                                           ModelMultipleChoiceFilter,
                                           NumberFilter)
from rest_framework import filters

from recipes.models import Ingredient, Recipe, Tag


class CustomFilterIngredient(filters.SearchFilter):
    """Фильтр для представления IngredientViewSet. Поиск по наимеенованию."""
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)


class CustomFilterRecipe(FilterSet):
    """
    Фильтр для представления RecipeViewSet.
    Поиск позволяет фильтровать по автору, тегам,
    включен ли рецепт в избранное пользователем
    и находится ли рецепт в корзине пользователя.
    """

    author = CharFilter(
        field_name='author__username'
    )
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'

    )
    is_favorited = NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = NumberFilter(
        method='filter_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр находится ли рецепт в избранном у пользователя."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite__user=user)

        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтр находится ли рецепт в корзине у пользователя."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_list__user=user)

        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
