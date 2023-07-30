from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, OuterRef
from drf_extra_fields.fields import Base64ImageField
from rest_framework import validators
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.serializers import (BooleanField, IntegerField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField, ReadOnlyField,
                                        ValidationError)

from api.users.serializers import UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


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
        fields = ('id', 'name', 'unit_of_measurement', 'amount', )


class RecipeIngredientCreateSerializer(ModelSerializer):
    """
    Сериализатор модели RecipeIngredient.
    Набор полей для сохранения и/или редактирования
    данных об ингредиентах в рецепте.
    Используется в сериализаторе RecipeSerializer и RecipePostSerializer
    В представлениях используется опосредованно через другие сериализаторы.
    """

    id = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'id')


class RecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe. Get. Набор полей и методов.
    используется в сериализаторе RecipePostSerializer
    в методе to_representation, и в сериализаторе FavoriteRecipeSerializer
    Используется в представлении RecipeViewSet для GET запросов.
    """

    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True,
        many=True,
        source='ingredients'
    )
    image = Base64ImageField()
    is_favorited = BooleanField(read_only=True, default=False)
    is_in_shopping_cart = BooleanField(read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image',
            'text', 'cooking_time', 'ingredients'
        )


class RecipePostSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe. POST. Набор полей и методов.
    Созданиеи-редактирование рецепта и добавление ингридиентов в рецепт.
    Используется в представлении RecipeViewSet для POST звпросов.
    """

    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'author',
            'image', 'name', 'text', 'cooking_time',
        )

    @transaction.atomic
    def add_ingredients(self, recipe, ingredients):
        """Атомарный метод добавления ингридиентов в рецепт."""
        ingredient_list_in_recipe = []
        for ingredient_data in ingredients:
            ingredient_list_in_recipe.append(
                RecipeIngredient(
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount'],
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
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        if ingredients is not None:
            instance.ingredients.clear()
            self.add_ingredients(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает сериализованные данные из метода RecipeSerializer."""
        request = self.context.get('request')

        return RecipeSerializer(instance, context={'request': request}).data


class RecipeShortSerializer(ModelSerializer):
    """
    Метод сокращенного рецепта для
    добавления в избранное и подписок.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteRecipeSerializer(ModelSerializer):
    """
    Сериализатор модели Favorite.
    Набор полей и метод определения рецепта в корзине покупок.
    Используется в представлении RecipeViewSet для метода favorite.
    """

    recipe = RecipeShortSerializer()

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe',)
        # убрала
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже находится в избранном.'
            )
        ]

    def create(self, validated_data):
        """
        Создает новый объект модели Favorite.
        """
        return Favorite.objects.create(**validated_data)


class ShoppingCartSerializer(ModelSerializer):
    """
    Предаставление модели ShoppingCart.
    Используется в прендставлении RecipeViewSet в методе shopping_cart.
    """

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def get_queryset(self):
        """
        Метод переопределяет стандартный метод get_queryset() модели.
        ДОбавляем дополнительное поле is_in_shopping_cart,
        которое указывает, находится ли рецепт в корзине покупок пользователя.
        """
        queryset = super().get_queryset()

        if self.context['request'].user.is_authenticated:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.context['request'].user,
                        recipe_id=OuterRef('pk')
                    )
                )
            )

        return queryset

    def validate(self, data):
        """
        Проверяет, что рецепт не был добавлен ранее.
        """
        queryset = self.get_queryset()

        if queryset.filter(recipe=data['recipe']
                           ).filter(is_in_shopping_cart=True).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')

        return data


class UserSubscribeSerializer(ModelSerializer):
    """
    Сериализатор модели автора, на которого подписался пользователь.
    Используется в представлении UsersViewSet в методах
    subscribe и subscriptions.
    """

    is_subscribed = SerializerMethodField()
    recipes = RecipeShortSerializer(many=True)
    recipes_count = ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'recipes_count', 'is_subscribed', 'recipes',)

    def validate(self, data):
        """
        Метод используется для проверки данных при создании нового объекта.
        """
        request = self.context.get('request')
        author = self.instance
        if request.user == author:
            raise ValidationError(
                'Вы не можете подписаться на самого себя.'
            )
        return data

    def get_is_subscribed(self, obj):
        """Метод наличия подписки на пользователя модели Subscription."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count
