from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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

    # def clean(self):
    #     if self.username == 'me':
    #         raise ValidationError('Имя me недоступно для регистрации')
    #     super(User, self).clean()
