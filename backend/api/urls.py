from django.urls import include, path

app_name = 'api'

urlpatterns = [
    path('api/', include('users.urls')),
    path('api/', include('recipes.urls')),
]
