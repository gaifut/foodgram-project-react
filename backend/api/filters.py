from django_filters import rest_framework as f


from recipes.models import Recipe


class RecipeFilter(f.FilterSet):
    author = f.CharFilter()
    tags = f.AllValuesMultipleFilter(
        field_name='tags__slug', lookup_expr='contains'
    )
    is_favorited = f.BooleanFilter()
    is_in_shopping_cart = f.BooleanFilter()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']