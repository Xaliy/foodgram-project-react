from django_filters.rest_framework import (BooleanFilter, FilterSet,
                                           ModelMultipleChoiceFilter)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """
    Фильтр для представления RecipeViewSet.
    Поиск позволяет фильтровать по автору, тегам,
    включен ли рецепт в избранное пользователем
    и находится ли рецепт в корзине пользователя.
    """

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'

    )
    is_favorited = BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = BooleanFilter(
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
