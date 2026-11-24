from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm
from .models import RolUsuario


def login(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data["nombre_usuario"]
            password = form.cleaned_data["password"]

            # Django mapea 'username' internamente a USERNAME_FIELD ('nombre_usuario')
            usuario = authenticate(request, username=nombre_usuario, password=password)

            if usuario is not None:
                auth_login(request, usuario)
                messages.success(request, f"Bienvenido, {usuario.nombre_usuario}.")

                # Redirección según rol (opcional)
                if usuario.rol == RolUsuario.ADMINISTRADOR:
                    return redirect("panel_admin")
                return redirect("seleccionar_clase")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


@login_required
def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("login")

def inicio(request):
    return redirect("seleccionar_clase")

def panel_admin(request):
    print("iniciaste sesion como administrador")
    