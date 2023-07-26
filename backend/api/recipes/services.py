from django.db.models import Sum
from recipes.models import RecipeIngredient


def get_shopping_list(user):
    """
    Функция для получения списока покупок пользователя.
    Используется в методе download_shopping_cart представления RecipeViewSet.
    """
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shopping_list__user=user)
        .order_by('ingredient__name')
        .values('ingredient__name', 'ingredient__unit_of_measurement')
        .annotate(amount=Sum('amount'))
    )

    shopping_list = []

    for ingredient in ingredients:
        shopping_list.append(
            f"{ingredient['ingredient__name']} "
            f"({ingredient['ingredient__unit_of_measurement']}) - "
            f"{ingredient['amount']}"
        )

    return '\n'.join(shopping_list)
