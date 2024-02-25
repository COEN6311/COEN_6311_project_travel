from rest_framework import permissions


class IsAgentPermission(permissions.BasePermission):
    """
    Custom permission to only allow agents of the site to access the method.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and is an agent
        return bool(request.user and request.user.is_authenticated and request.user.is_agent)
