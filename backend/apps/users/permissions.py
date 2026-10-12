from rest_framework.permissions import BasePermission


class HasCatalogAccess(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_perm("catalogs.view_revenueconcept")
            and request.user.has_perm("catalogs.view_collectionchannel")
        )


class HasLoadAccess(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        permission = "loads.add_revenueload" if request.method == "POST" else "loads.view_revenueload"
        return request.user.has_perm(permission)


class HasProgressionAccess(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        permission = "progression.change_progressionsettings" if request.method == "PATCH" else "progression.view_progressionsettings"
        return request.user.has_perm(permission)


class HasUserAdministrationAccess(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        permission = {
            "GET": "auth.view_user",
            "POST": "auth.add_user",
            "PATCH": "auth.change_user",
        }.get(request.method, "auth.view_user")
        return request.user.has_perm(permission)
