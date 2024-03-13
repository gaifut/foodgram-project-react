from django_filters import rest_framework as f

from recipes.models import Ingredient, Recipe


class RecipeFilter(f.FilterSet):
    author = f.CharFilter()
    tags = f.AllValuesMultipleFilter(
        field_name='tags__slug', lookup_expr='contains'
    )
    is_favorited = f.BooleanFilter(
        field_name='is_favorited',
        method='filter_is_favorited'
    )
    is_in_shopping_cart = f.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientFilter(f.FilterSet):
    name = f.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name', ]
