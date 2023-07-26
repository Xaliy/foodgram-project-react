from django.urls import include, path
from rest_framework import routers

from .views import UsersViewSet

app_name = 'users'

router_v_1 = routers.DefaultRouter()
router_v_1.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(router_v_1.urls)),
    # path('auth/', include('djoser.urls')),
    # path('auth/token/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]
