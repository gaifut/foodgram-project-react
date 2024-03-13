from django.db import models
from django.core.validators import (
    RegexValidator, MinValueValidator, MaxValueValidator)

from foodgram.constants import (
    CHARFIELD_MAX_LENGTH, COLOR_CHARS_MAX_LENGTH, POSITIVE_SMALL_MIN_VALUE,
    POSITIVE_SMALL_MAX_VALUE
)
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        verbose_name='Название тега',
        unique=True
    )
    color = models.CharField(
        max_length=COLOR_CHARS_MAX_LENGTH,
        unique=True,
        verbose_name='цвет',
        validators=(
            [RegexValidator(regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')]
        )
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=CHARFIELD_MAX_LENGTH,
        unique=True,
    )

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH, verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH, verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
    )
    name = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                POSITIVE_SMALL_MIN_VALUE,
                message='Значение не может быть меньше'
                f'{POSITIVE_SMALL_MIN_VALUE}'),
            MaxValueValidator(
                POSITIVE_SMALL_MAX_VALUE,
                message='Значение не может быть больше'
                f'{POSITIVE_SMALL_MAX_VALUE}')
        ]
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe')
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='business_logic/images/',
        default=None,
    )
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredients_recipe'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество',
        validators=[
            MinValueValidator(
                POSITIVE_SMALL_MIN_VALUE,
                message='Значение не может быть меньше'
                f'{POSITIVE_SMALL_MIN_VALUE}'),
            MaxValueValidator(
                POSITIVE_SMALL_MAX_VALUE,
                message='Значение не может быть больше'
                f'{POSITIVE_SMALL_MAX_VALUE}')
        ]
    )

    def __str__(self) -> str:
        return f'{self.ingredient} {self.recipe}'


class Subscription(models.Model):
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribed_to')
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriber')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribed_to'],
                name='unique_subscribed_to'
            )
        ]

    def __str__(self):
        return (
            f'{self.subscriber.username}'
            f' subscribed_to {self.subscribed_to.username}'
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite_user')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite_recipe'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart'
    )

    def __str__(self) -> str:
        return f'{self.user} {self.recipe}'
