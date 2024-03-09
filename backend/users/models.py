from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram.constants import MAX_LENGTH_VALUE


class User(AbstractUser):
    """Модель пользователя."""
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_VALUE,
        unique=True,
        validators=([UnicodeUsernameValidator()])
    )
    password = models.CharField(
        max_length=MAX_LENGTH_VALUE,
        verbose_name='Пароль'
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True)
    first_name = models.CharField(
        max_length=MAX_LENGTH_VALUE,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_VALUE,
        verbose_name='Фамилия'
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
