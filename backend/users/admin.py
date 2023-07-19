from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        # 'password',
    )
    list_filter = ('username', 'email',)
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.register(User, UserAdmin)
