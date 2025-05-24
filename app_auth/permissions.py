from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Chỉ cho phép admin (is_admin=True) truy cập.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_admin', False)
