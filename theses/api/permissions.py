"""
API PERMISSIONS.PY - API Access Control
========================================

This file defines CUSTOM PERMISSIONS for the REST API.
Permissions control WHO can do WHAT with API endpoints.

WHAT BELONGS HERE:
------------------
1. Custom permission classes
2. Access control logic for API endpoints
3. Object-level permission checks

WHAT ARE PERMISSIONS?
---------------------
Permissions answer the question: "Can this user perform this action?"

Django REST Framework checks permissions for every API request:
1. View-level permissions (has_permission): Can user access this endpoint?
2. Object-level permissions (has_object_permission): Can user access THIS specific object?

SAFE_METHODS:
-------------
SAFE_METHODS = GET, HEAD, OPTIONS (read-only methods that don't change data)
Unsafe methods = POST, PUT, PATCH, DELETE (write operations that change data)

COMMON PATTERN:
---------------
class MyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if user can access the endpoint at all
        return True  # or False

    def has_object_permission(self, request, view, obj):
        # Check if user can access this specific object
        if request.method in permissions.SAFE_METHODS:
            return True  # Anyone can read
        return obj.owner == request.user  # Only owner can edit

HOW PERMISSIONS ARE USED:
--------------------------
In viewsets.py:
    class MyViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, MyCustomPermission]
        # ALL permissions must pass (AND logic, not OR)

PERMISSION LOGIC:
-----------------
- If ANY permission returns False → Request is denied (403 Forbidden)
- ALL permissions must return True → Request is allowed
- Permissions are checked in the order they're listed

EXAMPLE:
--------
# In viewsets.py:
permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

# This means:
# 1. User must be logged in (IsAuthenticated)
# 2. AND user must own the object OR be making a read-only request
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Users can only edit their own objects.

    Used for: Comments (users can only edit their own comments)

    Logic:
    - Anyone (authenticated) can read (GET)
    - Only the owner can write (POST, PUT, PATCH, DELETE)

    Requires: The model must have a 'user' field linking to the owner
    """
    def has_object_permission(self, request, view, obj):
        """
        Check if user can access this specific object.

        Args:
            request: The HTTP request
            view: The ViewSet handling the request
            obj: The object being accessed (e.g., a Comment instance)

        Returns:
            bool: True if permission granted, False if denied
        """
        # SAFE_METHODS = GET, HEAD, OPTIONS (read-only)
        # Allow anyone to read
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations (POST, PUT, PATCH, DELETE):
        # Only allow if the object's user matches the request user
        return obj.user == request.user


class IsSupervisorOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Supervisors can edit theses they supervise.

    Used for: Theses (supervisors can edit the theses they supervise)

    Logic:
    - Anyone (authenticated) can read (GET)
    - Supervisors can edit theses they supervise
    - Staff users can edit any thesis

    Requires: The model must have a 'supervisors' ManyToMany field
    """
    def has_object_permission(self, request, view, obj):
        """
        Check if user can edit this thesis.

        The permission matches users to supervisors by email address.
        User's email must match a Supervisor's email in the thesis.
        """
        # Allow all read operations
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check if object has supervisors
        if hasattr(obj, 'supervisors'):
            # Match user to supervisor by email
            user_email = request.user.email
            if user_email:
                # Check if any supervisor has this email
                # .exists() is more efficient than .count() > 0
                return obj.supervisors.filter(email=user_email).exists()

        # Staff users can edit anything (fallback permission)
        return request.user.is_staff


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Only staff can create/edit/delete.

    Used for: Students, Supervisors (only staff can manage them)

    Logic:
    - Anyone (authenticated) can read (GET)
    - Only staff can write (POST, PUT, PATCH, DELETE)

    This prevents regular users from creating or modifying students/supervisors.
    """
    def has_permission(self, request, view):
        """
        View-level permission check.

        Note: This uses has_permission (not has_object_permission)
        because it checks access to the endpoint, not a specific object.

        Args:
            request: The HTTP request
            view: The ViewSet handling the request

        Returns:
            bool: True if permission granted, False if denied
        """
        # Allow authenticated users to read
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Only staff users can write
        # is_staff: Set in Django admin or programmatically
        return request.user and request.user.is_staff
