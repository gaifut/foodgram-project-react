from django.db import models
from django.core.validators import RegexValidator

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название тега')
    color = models.CharField(max_length=7, null=True, verbose_name='цвет')
    slug = models.CharField(
        verbose_name='Слаг тега',
        max_length=200,
        unique=True,
        validators=([RegexValidator(regex=r'^[-a-zA-Z0-9_]+$')])
    )

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='Название ингредиента', unique=True
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единица измерения'
    )

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
    )
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
    )
    ingredients = models.ManyToManyField(Ingredient)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='business_logic/images/',
        default=None,
    )
    published_at = models.DateTimeField(auto_now_add=True)
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredients_recipe'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients_recipe'
    )
    amount = models.IntegerField()

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
