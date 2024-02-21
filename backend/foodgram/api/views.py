from rest_framework import filters, generics, viewsets, status, permissions, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from business_logic.models import Ingredient, Recipe, Tag, Subscription
from users.models import User
from .serializers import (
    CustomUserSerializer, IngredientSerializer, RecipeSerializer, SubscriptionSerializer, TagSerializer
)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        queryset = User.objects.all()
        print("Queryset: ", queryset)
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({'ошибка': 'рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        

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







    
