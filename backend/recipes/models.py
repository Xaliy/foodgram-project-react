from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Класс тэги для рецептов."""

    name = models.CharField(
        verbose_name='Тег',
        max_length=60,
        unique=True,
        blank=False
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        unique=True,
        blank=False
    )
    slug = models.CharField(
        verbose_name='Слаг тэга, ссылка',
        max_length=150,
        unique=True,
        blank=False
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} цвет: {self.color}'


class Ingredient(models.Model):
    """Класс ингридиенты."""

    name = models.CharField(
        verbose_name='Наименование ингридиента',
        max_length=150,
        null=False,
        blank=False
    )
    unit_of_measurement = models.CharField(
        verbose_name='Единица измерения',
        max_length=50,
        null=False,
        blank=False
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return str(self.name)


class Recipe(models.Model):
    """Класс рецепты."""

    author = models.ForeignKey(
        User,  # класс
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=255
    )
    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='static/',
        blank=True,
        null=True
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        blank=True
    )
    ingredients = models.ManyToManyField(
        Ingredient,  # класс
        through='RecipeIngredient',  # уникальность
        verbose_name='Список ингредиентов'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(
                1, message='Время приготовления не менее 1 минуты'),
            MaxValueValidator(90, message='Долгое приготовление')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег рецепта',
        related_name='recipes'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Список рецептов'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.name} автор {self.author}'


class RecipeIngredient(models.Model):
    """Класс ингридиенты в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Колличество ингредиентов',
        validators=[
            MinValueValidator(
                1, message='Не менее 1 ингридиента'),
        ]
    )

    def __str__(self):
        return f"{self.ingredients} - {self.amount}"


class Favorite(models.Model):
    """Класс избранные рецепты."""

    user = models.ForeignKey(
        User,
        related_name='favorite',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        verbose_name='Избранный рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_user_recipe',
            ),
        ]

    def __str__(self):
        return f'{self.recipe} добавлен в избранное'


class ShoppingCart(models.Model):
    """Класс покупки."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping_list'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart_recipe_user',
            ),
        ]

    def __str__(self):
        return f'Рецепт {self.user} в избранном {self.recipe}'


class Subscription(models.Model):
    """Класс подписок."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='subscriptions',
        on_delete=models.CASCADE,
        help_text='Данный пользователь станет подписчиком автора'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Подписка автор',
        related_name='subscribers',
        on_delete=models.CASCADE,
        help_text='На автора могут подписаться другие пользователи',
    )

    class Meta:
        ordering = ('-id',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author'
            ),
        )
        verbose_name = 'Подписка',
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f"{self.user} подписка на {self.author}"
