from django_filters import rest_framework as f
from django.db.models import Exists, OuterRef


from recipes.models import Recipe, Favorite, ShoppingCart


class RecipeFilter(f.FilterSet):
    author = f.CharFilter()
    tags = f.AllValuesMultipleFilter(
        field_name='tags__slug', lookup_expr='contains'
    )
    is_favorited = f.BooleanFilter(field_name='is_favorited', method='filter_is_favorited')
    is_in_shopping_cart = f.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    # def filter_is_favorited(self, queryset, name, value):
    #     lookup = '__'.join([name, 'is_favorited'])
    #     return queryset.filter(**{lookup: value})
    
    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            subquery = Favorite.objects.filter(
                recipe=OuterRef('pk'),
            )
            queryset = queryset.annotate(
                is_favorited=Exists(subquery)
            )
            return queryset.filter(is_favorited=False)
        subquery = Favorite.objects.filter(
            recipe=OuterRef('pk'), user=self.request.user
        )
        queryset = queryset.annotate(
            is_favorited=Exists(subquery)
        )
        return queryset.filter(is_favorited=value)
    
    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            subquery = ShoppingCart.objects.filter(
                recipe=OuterRef('pk'),
            )
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(subquery)
            )
            return queryset.filter(is_in_shopping_cart=False)
        subquery = ShoppingCart.objects.filter(
            recipe=OuterRef('pk'), user=self.request.user
        )
        queryset = queryset.annotate(
            is_in_shopping_cart=Exists(subquery)
        )
        return queryset.filter(is_in_shopping_cart=value)