from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm, LoginForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from .models import Flower, Category, CartItem, Cart, Order, OrderItem
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from .utils import send_telegram_notification


# Create your views here.
def index(request):
    categories = Category.objects.all()
    return render(request, 'catalog/index.html', {'categories': categories})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Cart.objects.create(user=user)  # Создаем корзину
            login(request, user)
            return redirect('catalog_home')
    else:
        form = RegisterForm()
    return render(request, 'catalog/register.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'catalog/login.html'


class CustomLogoutView(LogoutView):
    http_method_names = ['post']


def catalog_home(request):
    if request.user.is_authenticated:
        flowers = Flower.objects.all()
        categories = Category.objects.all()
        return render(request, 'catalog/catalog_home.html', {'flowers': flowers, 'categories': categories})
    else:
        messages.warning(request, 'Для доступа к этой странице необходимо выполнить вход или зарегистрироваться')
        return render(request, 'catalog/index.html')


def category_flowers(request, category_id):
    if request.user.is_authenticated:
        category = get_object_or_404(Category, id=category_id)
        flowers = Flower.objects.filter(category=category)
        categories = Category.objects.all()
        return render(request, 'catalog/catalog_home.html', {'flowers': flowers, 'categories': categories})
    else:
        messages.warning(request, 'Для доступа к этой странице необходимо выполнить вход или зарегистрироваться')
        return render(request, 'catalog/index.html')


def add_to_cart(request, flower_id):
    flower = get_object_or_404(Flower, id=flower_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=request.user.cart,
        flower=flower,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('catalog_home')


class CartView(DetailView):
    model = Cart
    template_name = 'catalog/cart1.html'
    context_object_name = 'cart'

    def get_object(self):
        # Получаем корзину текущего пользователя
        return get_object_or_404(Cart, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.object

        # Рассчитываем общую сумму
        context['total_price'] = sum(
            item.flower.price * item.quantity
            for item in cart.items.all()
        )

        return context


class CheckoutView(CreateView):
    model = Order
    fields = ['delivery_address', 'phone', 'delivery_date', 'delivery_time']
    template_name = 'catalog/checkout.html'

    def form_valid(self, form):
        cart = self.request.user.cart
        order = form.save(commit=False)
        order.user = self.request.user
        order.total_price = sum(item.flower.price * item.quantity for item in cart.items.all())
        order.save()

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                flower=item.flower,
                quantity=item.quantity,
                price=item.flower.price
            )

        # Отправка уведомлений ДО очистки корзины и редиректа
        try:
            send_telegram_notification(order)
            self.send_order_email(order)
        except Exception as e:
            messages.error(self.request, f"Ошибка: неверный email адрес {order.user.email}. Письмо не отправлено.")

        cart.items.all().delete()
        return redirect('order_confirmation', pk=order.id)

        # Открываем модальное окно через сессию
        self.request.session['show_order_confirmation'] = order.id
        return redirect(reverse('catalog_home') + '?show_modal=true')

    def send_order_email(self, order):
        context = {
            'order': order,
            'site_url': self.request.build_absolute_uri('/')
        }
        html_message = render_to_string('emails/order_created.html', context)

        send_mail(
            subject=f'Заказ №{order.id} оформлен',
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[order.user.email],
            fail_silently=False
        )

class OrderConfirmationView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'catalog/order_confirmation.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Ограничиваем доступ только к заказам текущего пользователя"""
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Дополнительные данные для шаблона
        context['site_url'] = self.request.build_absolute_uri('/')
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'catalog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at').prefetch_related('orderitem_set__flower')
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        user.phone = request.POST.get('phone', '')
        user.address = request.POST.get('address', '')
        user.save()
        return redirect('profile')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'catalog/order_details.html'
    context_object_name = 'order'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['items'] = order.orderitem_set.select_related('flower')
        return context


def decrease_quantity(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=request.user.cart  # Защита от чужой корзины
    )
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def increase_quantity(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=request.user.cart
    )
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=request.user.cart
    )
    cart_item.delete()
    return redirect('cart')


def reorder(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user)

    for item in order.orderitem_set.all():
        if item.flower.in_stock:  # Проверяем наличие товара
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                flower=item.flower,
                defaults={'quantity': item.quantity}
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()

    messages.success(request, 'Товары из заказа добавлены в корзину!')
    return redirect('cart')


def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.can_cancel:
        order.status = 'canceled'
        order.save()
        messages.success(request, 'Заказ успешно отменен')
    else:
        messages.error(request, 'Невозможно отменить этот заказ')

    return redirect('profile')