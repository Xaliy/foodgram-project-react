from django.db.models import Sum
from recipes.models import RecipeIngredient


def get_shopping_list(user):
    """
    Функция для получения списока покупок пользователя.
    Используется в методе download_shopping_cart представления RecipeViewSet.
    """
    ingredients = (
        RecipeIngredient.objects
        .prefetch_related('recipe', 'ingredient')
        .filter(recipe__shopping_list__user=user)
        .values('ingredient__name', 'ingredient__unit_of_measurement')
        .annotate(amount=Sum('amount'))
    )

    shopping_list = '\n'.join([
        f"{ingredient['ingredient__name']} - {ingredient['amount']} "
        f"({ingredient['ingredient__unit_of_measurement']})"
        for ingredient in ingredients
    ])
    return f"Cписок покупок:\n{shopping_list}"
