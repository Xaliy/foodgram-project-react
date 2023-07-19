from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Класс предоставляет доступ только пользователям с правами
    администратора на все методы запроса.
    Неаутентифицированным разрешен только доступ на чтение.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
                and request.user.is_superuser)


class IsAuthor(permissions.BasePermission):
    """
    Класс проверяет является ли пользователь автором, если да, то
    разрешает действия. В противном случае доступ запрещен.
    """

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_superuser
                or obj.author == request.user)


class IsAdmin(permissions.BasePermission):
    """
    Класс разрешений предоставляет доступ только пользователям,
    являющимся аутентифицированным администратором.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
