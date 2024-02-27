# Generated by Django 3.2.16 on 2024-02-25 17:15

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название ингредиента')),
                ('measurement_unit', models.CharField(max_length=200, verbose_name='Единица измерения')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название тега')),
                ('color', models.CharField(max_length=7, null=True, verbose_name='цвет')),
                ('slug', models.CharField(max_length=200, unique=True, validators=[django.core.validators.RegexValidator(regex='^[-a-zA-Z0-9_]+$')], verbose_name='Слаг тега')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscribed_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribed_to', to=settings.AUTH_USER_MODEL)),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriber', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название рецепта')),
                ('text', models.TextField(verbose_name='Описание')),
                ('cooking_time', models.IntegerField(verbose_name='Время приготовления (в минутах)')),
                ('image', models.ImageField(default=None, upload_to='business_logic/images/', verbose_name='Изображение')),
                ('published_at', models.DateTimeField(auto_now_add=True)),
                ('is_favorited', models.BooleanField(default=False)),
                ('is_in_shopping_cart', models.BooleanField(default=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL)),
                ('ingredients', models.ManyToManyField(to='business_logic.Ingredient')),
                ('tags', models.ManyToManyField(to='business_logic.Tag')),
            ],
        ),
        migrations.CreateModel(
            name='IngredientRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_recipe', to='business_logic.ingredient')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_recipe', to='business_logic.recipe')),
            ],
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.UniqueConstraint(fields=('subscriber', 'subscribed_to'), name='unique_subscribed_to'),
        ),
    ]
