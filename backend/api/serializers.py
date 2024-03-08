from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError


from recipes.models import (
    Favorite, Ingredient, IngredientRecipe, Recipe,
    ShoppingCart, Subscription, Tag
)
from users.models import User


class MyBase64ImageField(Base64ImageField):
    def to_internal_value(self, base64_data):
        if not base64_data:
            raise ValidationError('Это поле не может быть пустым')
        return super().to_internal_value(base64_data)


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request and not request.user.is_anonymous
            and Subscription.objects.filter(
                subscriber=request.user,
                subscribed_to=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'name': data['name'],
            'measurement_unit': data['measurement_unit'],
            'amount': data['amount']
        }


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'name': data['name'],
            'measurement_unit': data['measurement_unit'],
            'amount': data['amount']
        }

    def to_internal_value(self, data):
        if isinstance(data, dict):
            ingredient_id = data.get('id')
            amount = data.get('amount')
            if ingredient_id is not None:
                return {'id': ingredient_id, 'amount': amount}
        return super().to_internal_value(data)

    def validate(self, data):
        id = data.get('id')
        if not Ingredient.objects.filter(id=id).exists():
            raise ValidationError('Объекта нет в базе.')
        amount = data.get('amount')
        if amount < 1:
            raise ValidationError('Количество должно быть не меньше 1')
        return data


class RecipeGetSerializer(serializers.ModelSerializer):
    image = MyBase64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeReadSerializer(
        many=True, source='ingredients_recipe'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        if request.user.is_anonymous:
            return False
        return bool(request and Favorite.objects.filter(
            user=request.user, recipe=obj.id
        ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if request.user.is_anonymous:
            return False
        return bool(request and ShoppingCart.objects.filter(
            user=request.user, recipe=obj.id
        ).exists())


class RecipeSerializer(serializers.ModelSerializer):
    image = MyBase64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeWriteSerializer(
        many=True, source='ingredients_recipe'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        if request.user.is_anonymous:
            return False
        return bool(request and Favorite.objects.filter(
            user=request.user, recipe=obj.id
        ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if request.user.is_anonymous:
            return False
        return bool(request and ShoppingCart.objects.filter(
            user=request.user, recipe=obj.id
        ).exists())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = TagSerializer(instance.tags.all(), many=True).data
        data['tags'] = tags
        return data

    def validate(self, data):
        ingredients_data = data.get('ingredients_recipe')
        if not ingredients_data:
            raise ValidationError('Список ингридиентов не может быть пустым.')
        check_unique_id = []
        for ingredient_data in ingredients_data:
            try:
                ingredient_id = ingredient_data.get('id')
                amount = ingredient_data.get('amount', 0)
                if amount < 1:
                    raise ValidationError(
                        'Кол-во ингридиентов должно быть > 1.'
                    )
            except ObjectDoesNotExist:
                raise ValidationError('Ингридиент должен быть в Базе Данных')
            check_unique_id.append(ingredient_id)
        if len(check_unique_id) != len(set(check_unique_id)):
            raise ValidationError('Ингридиенты должны быть уникальными.')

        tags_data = data.get('tags')
        if not tags_data:
            raise ValidationError('Список тегов не может быть пустым.')
        if len(tags_data) != len(set(tags_data)):
            raise ValidationError('Теги должны быть уникальными.')
        return data

    def create_ingredients(self, ingredients_data, recipe):
        ingredients_data_list = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients_data
        ]
        IngredientRecipe.objects.bulk_create(ingredients_data_list)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_recipe')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients_recipe')
        tags_data = validated_data.pop('tags')

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)

        ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            ingredient = Ingredient.objects.get(id=ingredient_id)
            ingredients.append(ingredient)
        instance.ingredients.set(ingredients)
        instance.tags.set(tags_data)

        return super().update(instance, validated_data)


class SubscirptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('subscribed_to', 'subscriber')

    def validate(self, attrs):
        if attrs.get('subscribed_to') == attrs.get('subscriber'):
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(
            subscribed_to=attrs.get('subscribed_to'),
            subscriber=attrs.get('subscriber')
        ).exists():
            raise ValidationError('Подписка уже существует.')
        return attrs


class DisplayRecipesSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscirptionRespondSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'recipes', 'is_subscribed',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            subscribed_to=obj,
            subscriber=self.context["request"].user
        ).exists()

    def get_recipes_count(self, user):
        return Recipe.objects.filter(
            author=user).count()

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=user)
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass

        return DisplayRecipesSubscriptionSerializer(
            recipes, many=True, context=self.context
        ).data


class ShoppingCartListSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeReadSerializer(
        many=True, source='ingredients_recipe'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('ingredients',)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в избранном.')
        return data


class FavoriteDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в корзине.')
        return data
