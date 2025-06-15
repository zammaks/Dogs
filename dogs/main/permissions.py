from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только суперпользователям.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser) 