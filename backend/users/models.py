from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя. Все атрибуты обязательны."""

    email = models.EmailField(
        verbose_name='E-mail',
        null=False,
        blank=False,
        max_length=150,
        unique=True
    )
    username = models.CharField(
        verbose_name='Логин пользователя',
        max_length=150,
        null=False,
        blank=False,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        verbose_name='Имя',
        null=False,
        blank=False,
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        null=False,
        blank=False,
        max_length=150,
    )
    password = models.CharField(
        max_length=128,
        verbose_name='Пароль'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='username_email'
            ),
        ]


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
