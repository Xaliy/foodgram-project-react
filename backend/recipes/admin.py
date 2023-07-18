from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')


class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit_of_measurement')
    search_fields = ('name',)
    list_filter = ('name',)

    def unit_of_measurement(self, obj):
        return obj.unit_of_measurement
    unit_of_measurement.short_description = 'Measurement Unit'


class RecipeIngredientAdmin(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'text',
        'cooking_time',
        'pub_date',
    )
    inlines = (RecipeIngredientAdmin,)
    search_fields = ('name', 'author')
    list_filter = ('author', 'name', 'tags',)
    readonly_fields = ('favorites',)

    def favorites(self, obj):
        return obj.favorite.count()


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)


admin.site.register(Tag, TagsAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
