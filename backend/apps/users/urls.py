from django.urls import path

from .views import (
    bootstrap_administrator,
    bootstrap_status,
    confirm_password_reset,
    csrf_cookie,
    current_user,
    request_password_reset,
    sign_in,
    sign_out,
    user_detail,
    users,
)


urlpatterns = [
    path("auth/csrf/", csrf_cookie, name="auth-csrf"),
    path("auth/login/", sign_in, name="auth-login"),
    path("auth/password-reset/", request_password_reset, name="auth-password-reset"),
    path("auth/password-reset/confirm/", confirm_password_reset, name="auth-password-reset-confirm"),
    path("auth/bootstrap/status/", bootstrap_status, name="auth-bootstrap-status"),
    path("auth/bootstrap/", bootstrap_administrator, name="auth-bootstrap"),
    path("auth/logout/", sign_out, name="auth-logout"),
    path("auth/me/", current_user, name="auth-me"),
    path("users/", users, name="users"),
    path("users/<int:user_id>/", user_detail, name="user-detail"),
]
