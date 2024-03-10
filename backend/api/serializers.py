from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError


from recipes.models import (
    Favorite, Ingredient, IngredientRecipe, Recipe,
    ShoppingCart, Subscription, Tag
)
from users.models import User


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
            request and request.user.is_authenticated
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
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
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
        return bool(request
                    and request.user.is_authenticated
                    and Favorite.objects.filter(
                        user=request.user, recipe=obj.id
                    ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return bool(request
                    and request.user.is_authenticated
                    and ShoppingCart.objects.filter(
                        user=request.user, recipe=obj.id
                    ).exists())


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeWriteSerializer(
        many=True, source='ingredients_recipe'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image',
        )

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        ingredients_data = data.get('ingredients_recipe')
        if not ingredients_data:
            raise ValidationError('Список ингридиентов не может быть пустым.')
        check_unique_id = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            check_unique_id.append(ingredient_id)
        if len(check_unique_id) != len(set(check_unique_id)):
            raise ValidationError('Ингридиенты должны быть уникальными.')
        tags_data = data.get('tags')
        if not tags_data:
            raise ValidationError('Список тегов не может быть пустым.')
        if len(tags_data) != len(set(tags_data)):
            raise ValidationError('Теги должны быть уникальными.')
        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value

    def create_ingredients(self, ingredients_data, recipe):
        ingredients_data_list = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
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

        self.create_ingredients(ingredients_data, instance)
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

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscirptionRespondSerializer(
            instance=instance.subscriber,
            context={'request': request}
        ).data


class DisplayRecipesSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscirptionRespondSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return bool(request
                    and request.user.is_authenticated
                    and Subscription.objects.filter(
                        subscribed_to=obj,
                        subscriber=request.user
                    ).exists())

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


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в избранном.')
        return data

    def to_representation(self, instance):
        return FavoriteDisplaySerializer(
            instance=instance.recipe,
        ).data


class FavoriteDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в корзине.')
        return data

    def to_representation(self, instance):
        return FavoriteDisplaySerializer(
            instance=instance.recipe,
        ).data
