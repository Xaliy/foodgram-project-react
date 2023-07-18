from rest_framework import permissions


class IsAdminAuthorOrReadOnly(permissions.BasePermission):
    """
    Класс разрешений предоставляет доступ на чтение и запись
    зарегестрированным пользователям, которые являются
    или автором объекта или админом, а также доступ только
    для чтения пользователям, неаутентифицированным,
    или не автор и не админ.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_superuser
                or obj.author == request.user)


class IsAdmin(permissions.BasePermission):
    """
    Класс разрешений предоставляет доступ только пользователям,
    прошедшим проверку подлинности и
    являющимся аутентифицированным администратором.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
