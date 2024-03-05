from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

MAX_LENGTH_VALUE = 150


class User(AbstractUser):
    """Модель пользователя."""
    USER = 'user'
    ADMIN = 'admin'
    USER_ROLES = [
        (USER, 'Авторизированный пользователь'),
        (ADMIN, 'Администратор'),
    ]
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_VALUE,
        unique=True,
        validators=([UnicodeUsernameValidator(regex=r'^[\w.@+-]+\Z')])
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
    role = models.CharField(
        verbose_name='Права доступа',
        max_length=MAX_LENGTH_VALUE,
        choices=USER_ROLES,
        default=USER
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def __str__(self):
        return self.username
