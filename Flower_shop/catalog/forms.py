
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import CustomUser, Order

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'phone', 'address')

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'phone', 'delivery_date', 'delivery_time']

    def clean_delivery_date(self):
        date = self.cleaned_data['delivery_date']
        if date < timezone.now().date():
            raise forms.ValidationError("Дата доставки не может быть в прошлом")
        return date