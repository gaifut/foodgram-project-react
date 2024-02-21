from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


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
        max_length=150,
        unique=True,
        validators=([RegexValidator(regex=r'^[\w.@+-]+\Z')])
    )
    password = models.CharField(max_length=150, verbose_name='Пароль')
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True)
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    role = models.CharField(
        verbose_name='Права доступа',
        max_length=150,
        choices=USER_ROLES,
        default=USER
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def __str__(self):
        return self.username
