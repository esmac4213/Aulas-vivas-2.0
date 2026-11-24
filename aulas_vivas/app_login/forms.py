from django import forms

class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(
        max_length=50,
        label="username",
        widget=forms.TextInput(attrs={"placeholder": "Tu usuario", "autofocus": True}),
    )
    password = forms.CharField(
        label="password",
        widget=forms.PasswordInput(attrs={"placeholder": "Tu contraseña"}),
    )