from rest_framework import filters, generics, viewsets, status, permissions, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.views import UserViewSet
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from business_logic.models import Ingredient, Recipe, Tag, Subscription
from users.models import User
from .serializers import (
    CustomUserSerializer, IngredientSerializer, RecipeSerializer,
    SubscriptionSerializer, TagSerializer, ShoppingCartSerializer,
    ShoppingCartListSerializer
)
from rest_framework.renderers import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        ingredients_info = {}

        if isinstance(data, list):
            for item in data:
                ingredients = item.get('ingredients', [])
                for ingredient in ingredients:
                    name = ingredient.get('name', '')
                    amount = ingredient.get('amount', 0)
                    measurement_unit = ingredient.get('measurement_unit', '')

                    if name in ingredients_info:
                        ingredients_info[name]['amount'] += amount
                    else:
                        ingredients_info[name] = {'amount': amount, 'measurement_unit': measurement_unit}

        else:
            ingredients = data.get('ingredients', [])
            for ingredient in ingredients:
                name = ingredient.get('name', '')
                amount = ingredient.get('amount', 0)
                measurement_unit = ingredient.get('measurement_unit', '')

                if name in ingredients_info:
                    ingredients_info[name]['amount'] += amount
                else:
                    ingredients_info[name] = {'amount': amount, 'measurement_unit': measurement_unit}

        ingredients_text = ''
        for name, info in ingredients_info.items():
            ingredients_text += f'{name}: {info["amount"]} {info["measurement_unit"]}\n'

        return ingredients_text

    # def render(self, data, media_type=None, renderer_context=None):
    #     ingredients_info = ''

    #     if isinstance(data, list):
    #         for item in data:
    #             ingredients = item.get('ingredients', [])
    #             for ingredient in ingredients:
    #                 name = ingredient.get('name', '')
    #                 amount = ingredient.get('amount', '')
    #                 measurement_unit = ingredient.get('measurement_unit', '')
    #                 ingredients_info += f'{name}: {amount} {measurement_unit}\n'
    #     else:
    #         ingredients = data.get('ingredients', [])
    #         for ingredient in ingredients:
    #             name = ingredient.get('name', '')
    #             amount = ingredient.get('amount', '')
    #             measurement_unit = ingredient.get('measurement_unit', '')
    #             ingredients_info += f'{name}: {amount} {measurement_unit}\n'

    #     return ingredients_info


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        queryset = User.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-published_at')
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags', 'is_favorited')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class FavoriteViewSet(viewsets.ModelViewSet):
    
    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_favorited = True
            recipe.save()
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({'ошибка': 'рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_favorited = False
            recipe.save()
            serializer = RecipeSerializer(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response({'ошибка': 'рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        

class ShoppingCartViewSet(viewsets.ModelViewSet):
    
    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_in_shopping_cart = True
            recipe.save()
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({'ошибка': 'рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_in_shopping_cart = False
            recipe.save()
            serializer = ShoppingCartSerializer(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response({'ошибка': 'рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        

class ShoppingCartListView(APIView): 
    renderer_classes = [PlainTextRenderer] 

    def get(self, request, *args, **kwargs):
        recipes = Recipe.objects.filter(is_in_shopping_cart=True)
        print("printing recipes: ", recipes)
        serializer = ShoppingCartListSerializer(recipes, many=True)
        response = Response(serializer.data)
        print("printing serialized response: ", response)

        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

 

class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return Subscription.objects.filter(subscriber=user)
    

class SubscriptionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def create (self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = True
        subscribed_to.save()
        subscriber = request.user

        serializer = self.get_serializer(data={
            'subscribed_to': subscribed_to.id,
            'subscriber': subscriber.id
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubscriptionView(APIView):
    def post(self, request, user_id):
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = True
        subscribed_to.save()
        subscriber = request.user

        serializer = SubscriptionSerializer(data={
            'subscribed_to': subscribed_to.id,
            'subscriber': subscriber.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = False
        
        subscriptions = Subscription.objects.filter(
            subscriber=request.user,
            subscribed_to=subscribed_to
        )
        
        subscriptions.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)







    
