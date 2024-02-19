from rest_framework import filters, viewsets
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend

from business_logic.models import Ingredient, Recipe, Tag, Subscription  #Favourite
from users.models import User
from .serializers import (
    CustomUserSerializer, IngredientSerializer, RecipeSerializer, SubscriptionSerializer, TagSerializer  # FavouriteSerializer
)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-published_at')
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer



class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    #filter_backends = [filters.SearchFilter]
    #search_fields = ['subscribe__username']

    # def get_queryset(self):
    #     return self.request.user.subscribed_to.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# class FavouriteViewSet(viewsets.ModelViewSet):
#     queryset = Favourite.objects.all()
#     serializer_class = FavouriteSerializer