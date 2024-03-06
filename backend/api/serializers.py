import base64

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError


from recipes.models import (
    Favorite, Ingredient, IngredientRecipe, Recipe, Subscription, Tag,
    ShoppingCart
)
from users.models import User


class MyBase64ImageField(Base64ImageField):
    def to_internal_value(self, base64_data):
        if not base64_data:
            raise ValidationError("This field could not be empty")
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
        return Favorite.objects.filter(
            user=obj.author, recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(
         user=obj.author, recipe=obj.id
        ).exists()


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
        return Favorite.objects.filter(
            user=obj.author, recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        print(type(obj))
        print(obj.__init__)
        return ShoppingCart.objects.filter(
         user=obj.author, recipe=obj.id
        ).exists()

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
                    raise ValidationError('Кол-во ингридиентов должно быть > 1.')
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
        print('VDDDD: ', validated_data)
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



class DisplayRecipesSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')



class SubscirptionRespondSerializer(CustomUserSerializer):
    # id = serializers.IntegerField(source='subscribed_to.id', read_only=True)
    # email = serializers.EmailField(
    #     source='subscribed_to.email', read_only=True
    # )
    # username = serializers.CharField(
    #     source='subscribed_to.username', read_only=True)
    # first_name = serializers.CharField(
    #     source='subscribed_to.first_name', read_only=True
    # )
    # last_name = serializers.CharField(
    #     source='subscribed_to.last_name', read_only=True
    # )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'recipes', 'is_subscribed',
            'recipes_count', 'subscribed_to', 'subscriber'  
        )
    
    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            subscribed_to=obj.subscribed_to,
            subscriber=obj.subscriber
        ).exists()

    def get_recipes_count(self, subscription):
        return Recipe.objects.filter(
            author=subscription.subscribed_to.id).count()

    def get_recipes(self, subscription):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=subscription.subscribed_to.id)
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass

        return DisplayRecipesSubscriptionSerializer(
            recipes, many=True, context=self.context
        ).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('subscribed_to')
        data.pop('subscriber')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    added_to_shopping_cart_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time', 'added_to_shopping_cart_by'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('added_to_shopping_cart_by')
        return data


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
        print('DATA IN VALIDATE METHOD', data)
        # recipe_id = self.context['request'].parser_context['kwargs']['recipe_pk']
        # user_id = self.context['request'].user.id
        # print(user_id)
        # print('recipe_id:', recipe_id)
        # try:
        #     recipe = Recipe.objects.get(id=recipe_id)
        #     if Favorite.objects.get(recipe_id=recipe_id, user_id=user_id).exists():
        #         raise ValidationError('Рецепт уже добавлен в избранное')
        # except Recipe.DoesNotExist:
        #     raise ValidationError('ошибка: рецепт не найден')
        return data


class FavoriteDisplaySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
