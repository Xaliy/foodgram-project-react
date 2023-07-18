from django.urls import include, path

app_name = 'api'

urlpatterns = [
    path('api/', include('api.users.urls')),
    path('api/', include('api.recipes.urls')),
]
