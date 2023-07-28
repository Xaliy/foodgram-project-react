from drf_extra_fields.fields import Base64ImageField
from django.db import transaction
from django.db.models import Exists, OuterRef
from djoser.serializers import UserSerializer as DjoserUserSerialiser
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription, Tag)
from rest_framework import validators
from rest_framework.exceptions import NotFound
from rest_framework.serializers import (BooleanField, IntegerField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)

from api.users.serializers import UserSerializer


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

    # id = ReadOnlyField(source='ingredient.id')
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = ReadOnlyField(source='ingredient.name')
    unit_of_measurement = ReadOnlyField(
        source='ingredient.unit_of_measurement'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',
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
    # id = ReadOnlyField(source='ingredient.id')
    # name = ReadOnlyField(source='ingredient.name')
    # unit_of_measurement = ReadOnlyField(
    #     source='ingredient.unit_of_measurement'
    # )

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
    # ingredients = RecipeIngredientSerializer(
    #     read_only=True,
    #     many=True,
    #     source='ingredients'
    # )
    ingredients = SerializerMethodField()
    is_favorited = BooleanField(read_only=True, default=False)
    is_in_shopping_cart = BooleanField(read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image',
            'text', 'cooking_time', 'ingredients'
        )

    def get_ingredients(self, obj):
        # ingredients = (
        #     RecipeIngredient.objects
        #     .select_related('recipe', 'ingredient')
        #     .filter(recipe=obj)
        # )
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe=obj)
        )
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.select_related(
                'user', 'recipe'
            ).filter(
                user=request.user, recipe_id=obj.id
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.select_related(
                'user', 'recipe'
            ).filter(
                user=request.user, recipe_id=obj
            ).exists()
        return False


class RecipePostSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe. POST. Набор полей и методов.
    Созданиеи-редактирование рецепта и добавление ингридиентов в рецепт.
    Используется в представлении RecipeViewSet для POST звпросов.
    """

    # id = ReadOnlyField()  # добавила - может вторая ошибка отседа!!!
    # author = UserSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'author',
            'image', 'name', 'text', 'cooking_time',
        )

    def add_ingredients(self, recipe, ingredients):
        """Метод добавления ингридиентов в рецепт."""
        # relations = []
        # for ingredient_data in ingredients:
        #     relations.append(RecipeIngredient(
        #         recipe=recipe,
        #         ingredient_id=ingredient_data['ingredient_id'],
        #         amount=ingredient_data['amount']
        #     ))
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingr.get('id'),
                amount=ingr.get('amount'),
            ) for ingr in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        """Атомарный метод создания рецепта с ингридиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request', None)
        recipe = Recipe.objects.create(author=author.user, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Атомарный метод редактирования рецепта."""
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает сериализованные данные из метода RecipeSerializer."""
        request = self.context.get('request')

        return RecipeSerializer(instance, context={'request': request}).data


# изменения - убрала валидатор добавила еще один класс  ReadFavoriteSerializer
# и через него метод to_representation
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
        # убрала
        # validators = [
        #     validators.UniqueTogetherValidator(
        #         queryset=Favorite.objects.all(),
        #         fields=['user', 'recipe'],
        #     )
        # ]

# добавила
    def to_representation(self, instance):
        return ReadFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


# добавила
class ReadFavoriteSerializer(ModelSerializer):
    """
    Сериализатор для чтения избранных рецептов.
    Используется в FavoriteRecipeSerializer.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeSerializer(ModelSerializer):
    """
    Сериализатор модели Subscription.
    Используется в представлении UsersViewSet в методах
    subscribe и subscriptions.
    """

    author = DjoserUserSerialiser(read_only=True)

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
        queryset = ShoppingCart.objects.all()

        if self.context['request'].auth:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.context['request'].auth.user,
                        recipe_id=OuterRef('pk')
                    )
                )
            )

        return queryset

    def validate(self, data):
        """
        Проверяет, что рецепт не был добавлен ранее.
        """
        if self.get_queryset().filter(recipe=data['recipe'],
                                      is_in_shopping_cart=True
                                      ).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')

        return data
