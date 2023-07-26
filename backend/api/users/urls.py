from django.urls import include, path

from .views import UserListView, UserSubscriptionView

urlpatterns = [
    path(
        'users/<int:id>/subscribe/',
        UserListView.as_view(),
        name='subscribe'
    ),
    path(
        'users/subscriptions/',
        UserSubscriptionView.as_view(),
        name='subscriptions'
    ),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]
