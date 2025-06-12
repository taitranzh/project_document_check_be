from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Chỉ cho phép admin (is_admin=True) truy cập.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_admin', False)


# class IsAdminOrReadOnlyPermission(IsAdminUser):
#     def has_permission(self, request, view):
#         return (
#             request.method in SAFE_METHODS
#             or super().has_permission(request, view)
#         )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Chỉ cho phép admin thực hiện các hành động ghi (POST, PUT, DELETE),
    còn lại (GET) thì ai cũng được xem.
    """

    def has_permission(self, request, view):
        # Nếu là thao tác chỉ đọc (GET, HEAD, OPTIONS) thì ai cũng được
        if request.method in permissions.SAFE_METHODS:
            return True
        # Nếu là thao tác ghi thì yêu cầu phải là admin
        return request.user.is_authenticated and getattr(request.user, 'is_admin', False)




