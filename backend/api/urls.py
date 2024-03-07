from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet,
    SubscriptionListView, SubscriptionView,
    ShoppingCartView, ShoppingCartListView, 
    FavoriteView  #FavoriteViewSet,
)
app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagViewSet, basename='tags')

# router_v1.register(
#     r'recipes/(?P<recipe_pk>\d+)/shopping_cart',
#     ShoppingCartViewSet,
#     basename='shopping_cart'
# )

# router_v1.register(
#     r'recipes/(?P<recipe_pk>\d+)/favorite',
#     FavoriteViewSet,
#     basename='favorites'
# )

urlpatterns = [
    path(
        'recipes/<int:recipe_pk>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='shopping_cart'
    ),
    path(
        'recipes/<int:recipe_pk>/favorite/',
        FavoriteView.as_view(),
        name='favorite-list'
    ),
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartListView.as_view(),
        name='shopping_cart-list'
    ),
    path(
        'users/subscriptions/',
        SubscriptionListView.as_view(),
        name='subscription-list'
    ),
    path(
        'users/<int:user_id>/subscribe/',
        SubscriptionView.as_view(),
        name='subscription'
    ),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
