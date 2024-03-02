import base64

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


from business_logic.models import (
    Tag, Ingredient, IngredientRecipe, Recipe, Subscription
)
from users.models import User
from business_logic.pagination import CustomPagination


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):

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


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')



class IngredientRecipeSerializer(serializers.ModelSerializer):
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


class RecipeGetSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredients_recipe'
    )
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image', 'is_favorited', 'is_in_shopping_cart'
        )


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredients_recipe'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    cooking_time = serializers.IntegerField(
        min_value=1,
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image', 'is_favorited', 'is_in_shopping_cart'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = TagSerializer(instance.tags.all(), many=True).data
        data['tags'] = tags
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_recipe')
        if ingredients_data == []:
            raise ValidationError('Список ингридиентов не может быть пустым.')
        tags_data = validated_data.pop('tags')
        if tags_data == []:
            raise ValidationError('Список тегов не может быть пустым.')
        recipe = Recipe.objects.create(**validated_data)

        if len(tags_data) != len(set(tags_data)):
            raise ValidationError('Теги должны быть уникальными.')

        check_unique_id = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            check_unique_id.append(ingredient_id)
        if len(check_unique_id) != len(set(check_unique_id)):
            raise ValidationError('Ингридиенты должны быть уникальными.')

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except ObjectDoesNotExist:
                raise ValidationError('Ингридиент должен быть в Базе Данных')
            amount = ingredient_data.get('amount', 0)
            if amount < 1:
                raise ValidationError('Кол-во ингридиентов должно быть > 1.')
            IngredientRecipe.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=amount
            )
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        if self.context['request'].user != instance.author:
            raise PermissionDenied
        try:
            ingredients_data = validated_data.pop('ingredients_recipe')
        except KeyError:
            raise ValidationError('Ингридиент должен быть в запросе.')
        if ingredients_data == []:
            raise ValidationError('Список ингридиентов не может быть пустым.')
        check_unique_id = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            check_unique_id.append(ingredient_id)
        if len(check_unique_id) != len(set(check_unique_id)):
            raise ValidationError('Ингридиенты должны быть уникальными.')

        try:
            tags_data = validated_data.pop('tags')
        except KeyError:
            raise ValidationError('Тег должен быть в запросе.')
        if tags_data == []:
            raise ValidationError('Список тегов не может быть пустым.')
        if len(tags_data) != len(set(tags_data)):
            raise ValidationError('Теги должны быть уникальными.')

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        lst_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except ObjectDoesNotExist:
                raise ValidationError('Ингридиент должен быть в Базе Данных')
            lst_ingredients.append(ingredient)
        instance.ingredients.set(lst_ingredients)
        amount = ingredient_data.get('amount', 0)
        if amount < 1:
            raise ValidationError('Кол-во ингридиентов должно быть > 1.')
        instance.tags.set(tags_data)

        instance.save()
        return instance


# class SubscriptionSerializer(serializers.ModelSerializer):
#     recipes = serializers.SerializerMethodField()
    

#     class Meta:
#         model = Subscription
#         fields = ('id', 'subscribed_to', 'subscriber', 'recipes')  #'recipes'
        
#     def get_recipes(self, obj):
#         request = self.context.get('request')
#         # recipes = Recipe.objects.filter(author=obj.author)
        
#         if request and not request.user.is_anonymous:
#             recipes_limit = request.query_params.get('recipes_limit')
#         recipes = obj.recipes.all()
#         if recipes_limit:
#             try:
#                 recipes = recipes[:int(recipes_limit)]
#             except TypeError:
#                 pass
#         return RecipeSerializer(
#             recipes, many=True, context=self.context
#         ).data

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data.pop('subscribed_to')
#         data.pop('subscriber')
#         data.pop('recipes')
#         subscribed_to = instance.subscribed_to
#         data['id'] = subscribed_to.id
#         data['email'] = subscribed_to.email
#         data['username'] = subscribed_to.username
#         data['first_name'] = subscribed_to.first_name
#         data['last_name'] = subscribed_to.last_name
#         data['is_subscribed'] = subscribed_to.is_subscribed
#         data['recipes_count'] = instance.subscribed_to.recipes.count()

#         recipes_data = []
#         for recipe in subscribed_to.recipes.all():
#             recipe_data = {
#                 'id': recipe.id,
#                 'name': recipe.name,
#                 'image': recipe.image.url,
#                 'cooking_time': recipe.cooking_time,
#             }
#             recipes_data.append(recipe_data)
#         data['recipes'] = recipes_data
#         return data
    
#     def validate(self, data):
#             subscriber = data.get('subscriber')
#             subscribed_to = data.get('subscribed_to')

#             if subscriber == subscribed_to:
#                 raise serializers.ValidationError('Нельзя подписаться на самого себя')

#             if Subscription.objects.filter(subscriber=subscriber, subscribed_to=subscribed_to).exists():
#                 raise serializers.ValidationError('Вы уже подписаны на данного пользователя.')

#             return data

class SubscirptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('subscribed_to', 'subscriber')
    
    def validate(self, data):
        subscriber = data.get('subscriber')
        subscribed_to = data.get('subscribed_to')

        if subscriber == subscribed_to:
            raise serializers.ValidationError('Нельзя подписаться на самого себя')

        if Subscription.objects.filter(subscriber=subscriber, subscribed_to=subscribed_to).exists():
            raise serializers.ValidationError('Вы уже подписаны на данного пользователя.')

        return data

class DisplayRecipesSubscriptionSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=1,
    )

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscirptionRespondSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='subscribed_to.id', read_only=True)
    email = serializers.EmailField(source='subscribed_to.email', read_only=True)
    username = serializers.CharField(source='subscribed_to.username', read_only=True)
    first_name = serializers.CharField(source='subscribed_to.first_name', read_only=True)
    last_name = serializers.CharField(source='subscribed_to.last_name', read_only=True)
    is_subscribed = serializers.BooleanField(source='subscribed_to.is_subscribed', read_only=True)
    recipes = serializers.SerializerMethodField()


    class Meta:
        model = Subscription
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'recipes', 'is_subscribed',
            'subscribed_to', 'subscriber',
        ) 

    def get_recipes(self, subscription):
        print('subscription: ', subscription)
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=subscription.subscribed_to.id)
        print('recipes first time: ', recipes)      
        print('request: ', request.__init__)
        if request and not request.user.is_anonymous:
            recipes_limit = request.query_params.get('recipes_limit')
            print('limit number: ', recipes_limit)
            if recipes_limit:
                try:
                    recipes = recipes[:int(recipes_limit)]
                    print('recipes final: ', recipes)
                except TypeError:
                    pass

        return DisplayRecipesSubscriptionSerializer(
            recipes, many=True, context=self.context
        ).data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data.pop('subscribed_to')
        data.pop('subscriber')

        data['recipes_count'] = instance.subscribed_to.recipes.count()

        return data



class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartListSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredients_recipe'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('ingredients',)


class FavoriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=1,
    )

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
