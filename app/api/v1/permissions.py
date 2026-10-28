from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrStaff(BasePermission):
    """Allow read access to everyone authenticated and writes to the owner/staff."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True

        owner_id = getattr(obj, 'user_id', None)
        if owner_id is None:
            diet_plan = getattr(obj, 'diet_plan', None)
            if diet_plan is not None:
                owner_id = diet_plan.user_id
        return owner_id == request.user.id
