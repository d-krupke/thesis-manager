from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user


class IsSupervisorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow supervisors to edit theses they supervise.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # For Thesis objects, check if user is a supervisor
        if hasattr(obj, 'supervisors'):
            # Get supervisor by user's email
            user_email = request.user.email
            if user_email:
                return obj.supervisors.filter(email=user_email).exists()

        # Staff users can edit anything
        return request.user.is_staff


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff users to edit.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to staff
        return request.user and request.user.is_staff
