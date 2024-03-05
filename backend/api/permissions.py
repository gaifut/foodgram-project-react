from rest_framework import permissions


# class IsAuthorAdminSuperuserOrReadOnlyPermission(permissions.BasePermission):
#     """Права доступа: автор, администратор,
#      суперпользователь или только чтение для SAFE_METHODS."""

#     def has_permission(self, request, view):
#         """Определяет права на уровне запроса и пользователя."""
#         return (request.method in permissions.SAFE_METHODS
#                 or request.user.is_authenticated)

#     def has_object_permission(self, request, view, obj):
#         """Определяет права на уровне объекта."""
#         return (request.method in permissions.SAFE_METHODS
#                 or request.user.is_admin())


# class IsAdminPermissionOrReadOnly(permissions.BasePermission):
#     """Права доступа: администратор или суперпользователь."""

#     def has_permission(self, request, view):
#         return (request.method in permissions.SAFE_METHODS
#                 or request.user.is_admin())


class IsRecipeAuthorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
