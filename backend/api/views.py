from rest_framework import (
    filters, viewsets, status, permissions,
)
from django.core.exceptions import PermissionDenied
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


from recipes.models import Ingredient, Recipe, Subscription, Tag
from api.pagination import CustomPagination
from users.models import User
from .filters import RecipeFilter
from .permissions import IsRecipeAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer, FavoriteSerializer,
    IngredientSerializer, RecipeGetSerializer, RecipeSerializer,
    ShoppingCartSerializer, ShoppingCartListSerializer,
    SubscirptionCreateSerializer, SubscirptionRespondSerializer, TagSerializer
)


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
    filterset_fields = ('name',)
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-published_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class FavoriteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = FavoriteSerializer

    # def create(self, request, *args, **kwargs):
    #     recipe_id = kwargs.get('recipe_pk')
    #     try:
    #         recipe = Recipe.objects.get(id=recipe_id)
    #         if recipe.is_favorited:
    #             return Response(
    #                 {'error': 'Рецепт уже добавлен в избранное'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         recipe.is_favorited = True
    #         recipe.favorited_by.add(request.user)
    #         recipe.save()
    #         serializer = FavoriteSerializer(
    #             recipe,
    #         )
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     except Recipe.DoesNotExist:
    #         return Response(
    #             {'ошибка': 'рецепт не найден'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    # def delete(self, request, *args, **kwargs):
    #     recipe_id = kwargs.get('recipe_pk')
    #     try:
    #         recipe = Recipe.objects.get(id=recipe_id)
    #         if (recipe.is_favorited and recipe
    #                 .favorited_by.filter(id=request.user.id).exists()):
    #             recipe.is_favorited = False
    #             recipe.favorited_by.remove(request.user)
    #             recipe.save()
    #             return Response(status=status.HTTP_204_NO_CONTENT)
    #         return Response({
    #             'error': 'Нельзя убрать из избранного рецепт,'
    #             ' которого там нет.'}, status=status.HTTP_400_BAD_REQUEST
    #         )
    #     except Recipe.DoesNotExist:
    #         return Response(
    #             {'ошибка': 'рецепт не найден'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get_object_or_404(id=recipe_id)
            if recipe.is_in_shopping_cart:
                return Response(
                    {'error': 'Рецепт уже есть в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe.is_in_shopping_cart = True
            recipe.added_to_shopping_cart_by.add(request.user)
            recipe.save()
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')

        try:
            recipe = Recipe.objects.get(id=recipe_id)
            if (recipe.is_in_shopping_cart
                and recipe.added_to_shopping_cart_by.filter(
                    id=request.user.id).exists()):
                recipe.is_in_shopping_cart = False
                recipe.added_to_shopping_cart_by.remove(request.user)
                recipe.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({
                'error': 'Нельзя удалить рецепт,'
                ' которого нет в корзине.'}, status=status.HTTP_400_BAD_REQUEST
            )
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingCartListView(APIView):
    renderer_classes = [PlainTextRenderer]
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = RecipeFilter

    def get(self, request, *args, **kwargs):
        recipes = Recipe.objects.filter(is_in_shopping_cart=True)
        serializer = ShoppingCartListSerializer(recipes, many=True)
        response = Response(serializer.data)
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class SubscriptionListView(ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscirptionRespondSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        queryset = Subscription.objects.filter(subscriber=user)
        recipes_limit = self.request.query_params.get('recipes_limit')
        if recipes_limit:
            queryset = queryset.annotate(recipes_count=Count(
                'subscribed_to__recipes'
            ))
            queryset = queryset.filter(recipes_count__lte=recipes_limit)

        return queryset


class SubscriptionView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination
    parser_classes = (IsAuthenticated,)


    def post(self, request, user_id):
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = True
        subscribed_to.save()
        subscriber = request.user

        queryset = User.objects.filter(following__user=self.request.user)

        serializer_create = SubscirptionCreateSerializer(
            data={
                'subscribed_to': subscribed_to.id,
                'subscriber': subscriber.id,
            })
        serializer_create.is_valid(raise_exception=True)
        subscription = serializer_create.save()

        serializer_respond = SubscirptionRespondSerializer(
            instance=subscription,
            context={'request': request}
        )
        return Response(
            serializer_respond.data, status=status.HTTP_201_CREATED
        )

    def delete(self, request, user_id):
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = False

        subscriptions = Subscription.objects.filter(
            subscriber=request.user,
            subscribed_to=subscribed_to
        )
        if subscriptions.exists():
            subscriptions.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'error': 'Нельзя удалить несуществующую подписку'},
            status=status.HTTP_400_BAD_REQUEST
        )
