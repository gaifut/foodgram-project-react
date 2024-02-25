from django.contrib import admin

from .models import Tag, Ingredient, Recipe, Subscription

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Subscription)
