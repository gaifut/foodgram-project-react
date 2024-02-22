import base64

from rest_framework import serializers
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer

from business_logic.models import Tag, Ingredient, IngredientRecipe, Recipe, Subscription
from users.models import User


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


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
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


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeSerializer(many=True, source='ingredients_recipe') #read_only=True, 
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    # is_favourited = FavouriteSerializer(many=True, source='favourites_recipe')

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time', 'image', 'is_favorited', 'is_in_shopping_cart'
        )


    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_recipe')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        
        if ingredients_data:
            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data.get('id')
                ingredient = Ingredient.objects.get(id=ingredient_id)
                amount = ingredient_data.get('amount', 0)
                IngredientRecipe.objects.create(
                    ingredient=ingredient,
                    recipe=recipe,
                    amount=amount
                )     
        if tags_data:
            recipe.tags.set(tags_data)
        return recipe
    
    def update(self, instance, validated_data):
        print("validated data:", validated_data)
        ingredients_data = validated_data.pop('ingredients_recipe')
        tags_data = validated_data.pop('tags')

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
        'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        

        lst_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            ingredient = Ingredient.objects.get(id=ingredient_id)
            lst_ingredients.append(ingredient)
        instance.ingredients.set(lst_ingredients)

        instance.tags.set(tags_data)

        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('id', 'subscribed_to', 'subscriber')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        subscribed_to = instance.subscribed_to
        data['id'] = subscribed_to.id
        data['email'] = subscribed_to.email
        data['username'] = subscribed_to.username
        data['first_name'] = subscribed_to.first_name
        data['last_name'] = subscribed_to.last_name
        data['is_subscribed'] = subscribed_to.is_subscribed
        data['recipes_count'] = instance.subscribed_to.recipes.count()

        recipes_data = []
        for recipe in subscribed_to.recipes.all():
            recipe_data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url,
                'cooking_time': recipe.cooking_time,
            }
            recipes_data.append(recipe_data)
        data['recipes'] = recipes_data

        return data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class ShoppingCartListSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True, source='ingredients_recipe')

    class Meta:
        model = IngredientRecipe
        fields = ('ingredients',)