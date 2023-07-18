from django.db import transaction

from djoser.serializers import UserSerializer

from rest_framework import validators
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)

from api.users.serializers import CustomUserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription, Tag)


class TagSerializer(ModelSerializer):
    """
    Сериализатор для модели Tag. Набор полей. Проверка уникальности.
    Испольуем в сериализаторе RecipeSerializer
    и представлении TagSerializer.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(ModelSerializer):
    """
    Сериализатор для модели Ingredient. Набор полей.
    Используется в представлении IngredientViewSet.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'unit_of_measurement',)


class RecipeIngredientSerializer(ModelSerializer):
    """
    Сериализатор для модели RecipeIngredient.
    Набор полей для получения данных о ингредиентах в рецепте.
    Используем в сериализатах RecipeSerializer и RecipePostSerializer.
    Во вьюхах опосредованно, черед другие сериализаторы.
    """

    id = IntegerField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    unit_of_measurement = ReadOnlyField(
        source='ingredient.unit_of_measurement'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'id',
                  'name', 'unit_of_measurement',)


class IngredientInRecipeSerializer(ModelSerializer):
    """
    Сериализатор модели RecipeIngredient.
    Набор полей для сохранения и/или редактирования
    данных об ингредиентах в рецепте.
    Используется в сериализаторе RecipeSerializer и RecipePostSerializer
    В представлениях используется опосредованно через другие сериализаторы.
    """

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.unit_of_measurement'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'id',
                  'name', 'unit_of_measurement',)


class RecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe. Get. Набор полей и методов.
    используется в сериализаторе RecipePostSerializer
    в методе to_representation, и в сериализаторе FavoriteRecipeSerializer
    Используется в представлении RecipeViewSet для GET запросов.
    """

    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True,
        many=True,
        source='ingredient_in_recipe'
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        """
        Метод добавления рецепта в избранное.
        Если пользователь авторизован и добавил рецепт в избранное.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

        return user.favorite.filter(recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Метод если пользователь авторизован проверяет
        есть ли рецепт в корзине.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

        return user.carts.filter(recipe=obj.id).exists()

    def get_ingredients(self, obj):
        """
        Метод создает новый IngredientInRecipeSerializer экземпляр
        и возвращает сериализованные данные.
        """
        ingredients = RecipeIngredient.objects.filter(recipe=obj)

        return IngredientInRecipeSerializer(ingredients, many=True).data


class RecipePostSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe. POST. Набор полей и методов.
    Созданиеи-редактирование рецепта и добавление ингридиентов в рецепт.
    Используется в представлении RecipeViewSet для POST звпросов.
    """

    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientInRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',
        )

    @transaction.atomic
    def add_ingredients(recipe, ingredients):
        """Атомарный метод добавления ингридиентов в рецепт."""
        ingredient_list_in_recipe = []
        for ingredient_data in ingredients:
            ingredient_list_in_recipe.append(
                RecipeIngredient(
                    ingredient=ingredient_data.pop('id'),
                    amount=ingredient_data.pop('amount'),
                    recipe=recipe,
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list_in_recipe)

    @transaction.atomic
    def create(self, validated_data):
        """Атомарный метод создания рецепта с ингридиентами."""
        request = self.context.get('request', None)
        if not request.user.is_authenticated:
            raise PermissionDenied(
                detail='Вы должны быть зарегистрированы, чтобы создать рецепт.'
                )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Атомарный метод редактирования рецепта."""
        if not instance.is_active:
            raise NotFound(detail='Рецепт не найден')
        tags = validated_data.get('tags', instance.tags)
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
            self.add_ingredients(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает сериализованные данные из метода RecipeSerializer."""
        request = self.context.get('request')

        return RecipeSerializer(instance, context={'request': request}).data


class FavoriteRecipeSerializer(ModelSerializer):
    """
    Сериализатор модели Favorite.
    Набор полей и метод определения рецепта в корзине покупок.
    Используется в представлении RecipeViewSet для метода favorite.
    """

    recipe = RecipeSerializer()

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
            )
        ]

    def create(self, validated_data):
        """
        Создает новый объект модели Favorite.
        """
        return Favorite.objects.create(**validated_data)


class UserSubscribeSerializer(ModelSerializer):
    """
    Сериализатор модели Subscription.
    Используется в представлении UsersViewSet в методах
    subscribe и subscriptions.
    """

    author = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Уже есть подписка на этого пользователя.'
            )
        ]

    def validate(self, data):
        """
        Метод используется для проверки данных при создании нового объекта.
        """
        request = self.context.get('request')
        if request.user == data['author']:
            raise ValidationError('Вы не можете подписаться на самого себя.')
        return data


class ShoppingCartSerializer(ModelSerializer):
    """
    Предаставление модели ShoppingCart.
    Используется в прендставлении RecipeViewSet в методе shopping_cart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        """
        Проверяет, что рецепт не был добавлен ранее.
        """
        if ShoppingCart.objects.filter(user=data['user'],
                                       recipe=data['recipe']
                                       ).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')

        return data
