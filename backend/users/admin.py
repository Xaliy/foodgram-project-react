from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import TokenProxy

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
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

    admin.site.unregister(TokenProxy)
