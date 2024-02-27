from rest_framework import (
    filters, generics, viewsets, status, permissions, mixins
)
from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


from business_logic.models import Ingredient, Recipe, Tag, Subscription
from business_logic.pagination import CustomPagination
from users.models import User
from .permissions import IsAuthorAdminSuperuserOrReadOnlyPermission, IsAdminPermissionOrReadOnly
from .serializers import (
    CustomUserSerializer, IngredientListSerializer, IngredientSerializer, RecipeSerializer, RecipeGetSerializer,
    ShoppingCartSerializer, ShoppingCartListSerializer, SubscriptionSerializer,
    TagSerializer
)
from django_filters import rest_framework as f


class RecipeFilter(f.FilterSet):
    author = f.CharFilter(field_name='author__username')
    tags = f.CharFilter(field_name='tags__slug') 
    is_favorited = f.BooleanFilter(field_name='is_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited']


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
                        ingredients_info[name] = {
                            'amount': amount,
                            'measurement_unit': measurement_unit
                        }

        else:
            ingredients = data.get('ingredients', [])
            for ingredient in ingredients:
                name = ingredient.get('name', '')
                amount = ingredient.get('amount', 0)
                measurement_unit = ingredient.get('measurement_unit', '')

                if name in ingredients_info:
                    ingredients_info[name]['amount'] += amount
                else:
                    ingredients_info[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }

        ingredients_text = ''
        for name, info in ingredients_info.items():
            ingredients_text += (
                f'{name}: {info["amount"]} {info["measurement_unit"]}\n'
            )

        return ingredients_text


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return IngredientListSerializer
        return IngredientSerializer



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-published_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    #filterset_fields = ('author', 'tags', 'is_favorited', 'name')
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class FavoriteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorAdminSuperuserOrReadOnlyPermission,)

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_favorited = True
            recipe.save()
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_favorited = False
            recipe.save()
            # serializer = RecipeSerializer(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorAdminSuperuserOrReadOnlyPermission,)

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_in_shopping_cart = True
            recipe.save()
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe.is_in_shopping_cart = False
            recipe.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingCartListView(APIView):
    renderer_classes = [PlainTextRenderer]
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        recipes = Recipe.objects.filter(is_in_shopping_cart=True)
        print("printing recipes: ", recipes)
        serializer = ShoppingCartListSerializer(recipes, many=True)
        response = Response(serializer.data)
        print("printing serialized response: ", response)

        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
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

    def create(self, request, *args, **kwargs):
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
