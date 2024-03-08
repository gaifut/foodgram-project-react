from rest_framework import (
    filters, viewsets, status, permissions,
)
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.views import APIView


from recipes.models import (
    Favorite, Ingredient, IngredientRecipe,
    Recipe, ShoppingCart, Subscription, Tag
)
from api.pagination import CustomPagination
from users.models import User
from .filters import RecipeFilter
from .permissions import IsRecipeAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer, FavoriteSerializer,
    IngredientSerializer, RecipeGetSerializer, RecipeSerializer,
    ShoppingCartSerializer, SubscirptionCreateSerializer,
    SubscirptionRespondSerializer, TagSerializer,
    FavoriteDisplaySerializer
)


def make_file(ingredients):
    ingredients_info = []
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        amount = ingredient['ingredient__measurement_unit']
        measurement_unit = ingredient['total_qty']
        ingredients_info.append(f'{name}: {amount} {measurement_unit}')
    content = '\n'.join(ingredients_info)
    response = FileResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
    return response


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


class ShoppingCartListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = RecipeFilter

    def get(self, request, *args, **kwargs):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_qty=Sum('amount')
        )

        return make_file(ingredients)


class SubscriptionListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = SubscirptionRespondSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)


class SubscriptionView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = SubscirptionRespondSerializer

    def post(self, request, user_id):
        subscribed_to = get_object_or_404(User, pk=user_id)
        subscribed_to.is_subscribed = True
        subscribed_to.save()
        subscriber = request.user

        serializer_create = SubscirptionCreateSerializer(
            data={
                'subscribed_to': subscribed_to.id,
                'subscriber': subscriber.id,
            })
        serializer_create.is_valid(raise_exception=True)
        serializer_create.save()

        serializer_respond = SubscirptionRespondSerializer(
            instance=get_object_or_404(User, pk=user_id),
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


class FavoriteView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def post(self, request, recipe_pk):
        user_id = request.user.id
        serializer_create = FavoriteSerializer(
            data={
                'user': user_id,
                'recipe': recipe_pk,
            }
        )
        serializer_create.is_valid(raise_exception=True)
        favorite = serializer_create.save()

        serializer_respond = FavoriteDisplaySerializer(
            instance=favorite.recipe,
        )
        return Response(
            serializer_respond.data, status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_pk):
        user_id = request.user.id
        favorites = Favorite.objects.filter(
            user=user_id,
            recipe=recipe_pk
        )
        if not Recipe.objects.filter(pk=recipe_pk).exists():
            raise NotFound('Рецепта не существует.')
        if not favorites.exists():
            return Response({
                'error': 'рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorites.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def post(self, request, recipe_pk):
        user_id = request.user.id
        serializer_create = ShoppingCartSerializer(
            data={
                'user': user_id,
                'recipe': recipe_pk,
            }
        )
        serializer_create.is_valid(raise_exception=True)
        shopping_cart = serializer_create.save()

        serializer_respond = FavoriteDisplaySerializer(
            instance=shopping_cart.recipe,
        )
        return Response(
            serializer_respond.data, status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_pk):
        user_id = request.user.id
        shopping_cart = ShoppingCart.objects.filter(
            user=user_id,
            recipe=recipe_pk
        )
        if not Recipe.objects.filter(pk=recipe_pk).exists():
            raise NotFound('Рецепта не существует.')

        if not shopping_cart.exists():
            return Response({
                'error': 'рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
