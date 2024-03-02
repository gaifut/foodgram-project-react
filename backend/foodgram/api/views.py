import pprint
from rest_framework import (
    filters, generics, viewsets, status, permissions, mixins
)
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView


from business_logic.models import Ingredient, Recipe, Tag, Subscription
from business_logic.pagination import CustomPagination
from users.models import User
from .permissions import IsAuthorAdminSuperuserOrReadOnlyPermission
from .serializers import (
    CustomUserSerializer, IngredientListSerializer, IngredientSerializer, RecipeSerializer, RecipeGetSerializer,
    ShoppingCartSerializer, ShoppingCartListSerializer,
    TagSerializer, FavoriteSerializer, SubscirptionCreateSerializer, SubscirptionRespondSerializer  #, SubscriptionListSerializer, SubscriptionCreateSerializer
)
from django_filters import rest_framework as f



class RecipeFilter(f.FilterSet):
    author = f.CharFilter()
    tags = f.AllValuesMultipleFilter(field_name='tags__slug', lookup_expr='contains')
    is_favorited = f.BooleanFilter()
    is_in_shopping_cart = f.BooleanFilter()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']


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

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return IngredientListSerializer
        return IngredientSerializer



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-published_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # @action(detail=True, permission_classes=[IsAuthenticated], methods=['POST'])
    # def add_to_favorites(self, request, *args, **kwargs):
    #     recipe_id = kwargs.get('pk')
    #     try:
    #         recipe = Recipe.objects.get(id=recipe_id)
    #         if recipe.is_favorited:
    #             return Response(
    #                 {'error': 'Рецепт уже добавлен в избранное'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         recipe.is_favorited = True
    #         recipe.save()
    #         serializer = FavoriteSerializer(recipe)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     except Recipe.DoesNotExist:
    #         return Response(
    #             {'ошибка': 'рецепт не найден'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    # @action(detail=True, permission_classes=[IsAuthenticated], methods=['DELETE'])
    # def remove_from_favorites(self, request, *args, **kwargs):
    #     recipe_id = kwargs.get('pk')
    #     try:
    #         recipe = Recipe.objects.get(id=recipe_id)
    #         if not recipe.is_favorited:
    #             return Response(
    #                 {'error': 'Рецепт не был добавлен в избранное'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         recipe.is_favorited = False
    #         recipe.save()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     except Recipe.DoesNotExist:
    #         return Response(
    #             {'ошибка': 'рецепт не найден'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.author:
            raise PermissionDenied('Удалять рецепт может только автор рецепта.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
            if recipe.is_favorited:
                return Response(
                    {'error': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe.is_favorited = True
            recipe.save()
            serializer = FavoriteSerializer(
                recipe,
                ) 
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
            recipe.is_favorited = False
            recipe.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorAdminSuperuserOrReadOnlyPermission,)

    # def get_queryset(self):
    #     user = self.request.user
    #     queryset = Recipe.objects.filter(shopping_cart_users=user, is_in_shopping_cart=True)
    #     return queryset

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            if recipe.is_in_shopping_cart:
                return Response(
                    {'error': 'Рецепт уже есть в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe.is_in_shopping_cart = True
            recipe.save()
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response(
                {'ошибка': 'рецепт не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )


    def delete(self, request, *args, **kwargs):
        print(self.__init__)
        recipe_id = kwargs.get('recipe_pk')

        try:
            recipe = Recipe.objects.get(id=recipe_id)
            print(recipe)
            print(recipe.is_in_shopping_cart)
            # if not recipe.is_in_shopping_cart:
            #     return Response(
            #         {'error': 'Нельзя удалить рецепт, которого нет в корзине.'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
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
        print(queryset)

        recipes_limit = self.request.query_params.get('recipes_limit')
        if recipes_limit:
            queryset = queryset.annotate(recipes_count=Count('subscribed_to__recipes'))
            queryset = queryset.filter(recipes_count__lte=recipes_limit)

        return queryset


class SubscriptionView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def post(self, request, user_id):
        pprint.pprint(request.__dict__)
        print('user_id: ', user_id)
        print('self: ', self.__dict__)
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
        subscription = serializer_create.save()

        serializer_respond = SubscirptionRespondSerializer(
            instance=subscription,
            context={'request': request}
            )
        print('serializer_respond_contents: ',serializer_respond.__init__)
        return Response(serializer_respond.data, status=status.HTTP_201_CREATED)


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
        return Response(
                    {'error': 'Нельзя удалить несуществующую подписку'},
                    status=status.HTTP_400_BAD_REQUEST
                )
