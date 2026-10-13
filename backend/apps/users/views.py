from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .permissions import HasUserAdministrationAccess


ROLE_NAMES = ("ADMINISTRADOR", "SUPERVISOR", "OPERADOR")


def serialize_user(user):
    full_name = user.get_full_name().strip() or user.username
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "roles": list(user.groups.filter(name__in=ROLE_NAMES).values_list("name", flat=True)),
        "permissions": sorted(user.get_all_permissions()),
        "last_login": user.last_login,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_cookie(request):
    return Response({"detail": "Cookie CSRF preparada"})


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return Response({"error": "Usuario o contraseña incorrectos"}, status=400)
    login(request, user)
    return Response(serialize_user(user))


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = str(request.data.get("email", "")).strip().lower()
    user = get_user_model().objects.filter(email__iexact=email, is_active=True).first() if email else None
    if user and user.has_usable_password():
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base_url = settings.APP_PUBLIC_URL or request.build_absolute_uri("/").rstrip("/")
        reset_url = f"{base_url}/#restablecer?uid={uid}&token={token}"
        send_mail(
            "Restablecer contraseña de Recaudación",
            (
                f"Hola {user.get_full_name().strip() or user.username},\n\n"
                "Recibimos una solicitud para cambiar tu contraseña. "
                "Abrí este enlace para elegir una nueva:\n\n"
                f"{reset_url}\n\n"
                "Si no solicitaste el cambio, ignorá este mensaje."
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    return Response({"detail": "Si el correo está registrado, recibirás un enlace para restablecer la contraseña."})


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    uid = str(request.data.get("uid", ""))
    token = str(request.data.get("token", ""))
    password = str(request.data.get("password", ""))
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        user = None
    if not user or not default_token_generator.check_token(user, token):
        return Response({"error": "El enlace no es válido o ya venció"}, status=400)
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return Response({"error": " ".join(exc.messages)}, status=400)
    user.set_password(password)
    user.save(update_fields=("password",))
    return Response({"detail": "La contraseña fue actualizada correctamente."})


@api_view(["GET"])
@permission_classes([AllowAny])
def bootstrap_status(request):
    required = not get_user_model().objects.exists()
    return Response({"required": required, "available": bool(required and settings.DEBUG)})


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def bootstrap_administrator(request):
    User = get_user_model()
    if not settings.DEBUG or User.objects.exists():
        return Response({"error": "La inicialización ya no está disponible"}, status=403)
    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))
    email = str(request.data.get("email", "")).strip().lower()
    if not username or not password or not email:
        return Response({"error": "Usuario, correo y contraseña son obligatorios"}, status=400)
    try:
        validate_password(password)
        with transaction.atomic():
            if User.objects.select_for_update().exists():
                raise ValueError("La inicialización ya fue realizada")
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=str(request.data.get("first_name", "")).strip(),
                last_name=str(request.data.get("last_name", "")).strip(),
            )
            assign_role(user, "ADMINISTRADOR")
    except (ValidationError, ValueError) as exc:
        message = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
        return Response({"error": " ".join(message)}, status=400)
    login(request, user)
    return Response(serialize_user(user), status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sign_out(request):
    logout(request)
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(serialize_user(request.user))


def assign_role(user, role_name):
    if role_name not in ROLE_NAMES:
        raise ValueError("Rol inválido")
    role = Group.objects.filter(name=role_name).first()
    if not role:
        raise ValueError("Los roles todavía no fueron inicializados")
    user.groups.remove(*Group.objects.filter(name__in=ROLE_NAMES))
    user.groups.add(role)


@api_view(["GET", "POST"])
@permission_classes([HasUserAdministrationAccess])
def users(request):
    User = get_user_model()
    if request.method == "GET":
        queryset = User.objects.prefetch_related("groups").order_by("username")
        return Response({"users": [serialize_user(user) for user in queryset], "roles": ROLE_NAMES})

    required = ("username", "email", "password", "role")
    missing = [field for field in required if not str(request.data.get(field, "")).strip()]
    if missing:
        return Response({"error": f"Faltan campos obligatorios: {', '.join(missing)}"}, status=400)
    username = str(request.data["username"]).strip()
    if User.objects.filter(username__iexact=username).exists():
        return Response({"error": "El nombre de usuario ya existe"}, status=400)
    email = str(request.data.get("email", "")).strip().lower()
    if email and User.objects.filter(email__iexact=email).exists():
        return Response({"error": "El correo electrónico ya está registrado"}, status=400)
    password = str(request.data["password"])
    try:
        validate_password(password)
        with transaction.atomic():
            user = User(
                username=username,
                email=email,
                first_name=str(request.data.get("first_name", "")).strip(),
                last_name=str(request.data.get("last_name", "")).strip(),
                is_active=True,
            )
            user.set_password(password)
            user.full_clean(exclude=("password", "last_login", "date_joined"))
            user.save()
            assign_role(user, str(request.data["role"]))
    except (ValidationError, ValueError) as exc:
        message = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
        return Response({"error": " ".join(message)}, status=400)
    return Response(serialize_user(user), status=201)


@api_view(["PATCH"])
@permission_classes([HasUserAdministrationAccess])
def user_detail(request, user_id):
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return Response({"error": "Usuario no encontrado"}, status=404)
    if user.pk == request.user.pk and request.data.get("is_active") is False:
        return Response({"error": "No puede desactivar su propio usuario"}, status=400)
    try:
        with transaction.atomic():
            for field in ("first_name", "last_name", "email"):
                if field in request.data:
                    value = str(request.data[field]).strip()
                    setattr(user, field, value.lower() if field == "email" else value)
            if user.email and User.objects.filter(email__iexact=user.email).exclude(pk=user.pk).exists():
                raise ValueError("El correo electrónico ya está registrado")
            if "is_active" in request.data:
                if not isinstance(request.data["is_active"], bool):
                    raise ValueError("is_active debe ser verdadero o falso")
                user.is_active = request.data["is_active"]
            if request.data.get("password"):
                password = str(request.data["password"])
                validate_password(password, user=user)
                user.set_password(password)
            user.full_clean(exclude=("password", "last_login", "date_joined"))
            user.save()
            if "role" in request.data:
                assign_role(user, str(request.data["role"]))
    except (ValidationError, ValueError) as exc:
        message = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
        return Response({"error": " ".join(message)}, status=400)
    return Response(serialize_user(user))
