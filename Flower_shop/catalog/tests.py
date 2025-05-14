# test_models
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Flower, Order

class ModelTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='+79123456789',
            address='Test Address'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_product_creation(self):
        product = Flower.objects.create(
            name='Rose Bouquet',
            price=2999.99
        )
        self.assertEqual(str(product), 'Rose Bouquet')

    def test_order_creation(self):
        user = get_user_model().objects.create_user('user@example.com', 'test123')
        product = Flower.objects.create(name='Tulips', price=1500.00)
        order = Order.objects.create(user=user)
        order.products.add(product)

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, 1500.00)


# test_views
from django.test import Client
from django.urls import reverse

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='test@user.com',
            password='testpass123',
            phone='+79123456789'
        )
        self.product = Flower.objects.create(
            name='Test Bouquet',
            price=2500.00
        )

    def test_catalog_view(self):
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Bouquet')

    def test_order_flow(self):
        # Login
        self.client.login(email='test@user.com', password='testpass123')

        # Add to cart
        response = self.client.post(reverse('add-to-cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

        # Checkout
        checkout_data = {
            'delivery_address': 'Test Address',
            'delivery_time': '2024-03-20 15:00'
        }
        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)


# test_integration
from unittest.mock import patch
from django.core import mail


class IntegrationTests(TestCase):
    @patch('utils.send_telegram_notification')  # Мок для уведомления администратора в Telegram
    def test_full_order_cycle(self, mock_admin_notify):
        # 1. Регистрация нового пользователя (без Telegram chat ID)
        self.client.post(reverse('register'), {
            'email': 'new@user.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'phone': '+79123456789',
            'address': 'Integration Test Address'
        })

        # 2. Авторизация и создание товара
        self.client.login(email='new@user.com', password='complexpass123')
        product = Flower.objects.create(name='Integration Bouquet', price=3000.00)

        # 3. Добавление в корзину и оформление заказа
        self.client.post(reverse('add-to-cart', args=[product.id]))
        response = self.client.post(reverse('checkout'), {
            'delivery_address': 'New Address',
            'delivery_time': '2024-03-21 12:00'
        })

        # Проверка создания заказа
        order = Order.objects.first()
        self.assertEqual(order.status, 'pending')

        # 4. Проверка уведомления администратора в Telegram
        mock_admin_notify.assert_called_once_with(
            f"New order #{order.id}\n"
            f"Product: Integration Bouquet\n"
            f"Total: 3000.00"
        )

        # 5. Админ изменяет статус заказа
        admin = get_user_model().objects.create_superuser('admin@example.com', 'adminpass')
        self.client.force_login(admin)
        self.client.post(reverse('admin:flowers_order_change', args=[order.id]), {
            'status': 'delivered'
        })

        # 6. Проверка отправки email пользователю
        self.assertEqual(len(mail.outbox), 1)  # Проверяем что письмо отправлено
        email = mail.outbox[0]

        self.assertEqual(email.to, ['new@user.com'])
        self.assertIn(f'Order #{order.id} status changed to delivered', email.subject)
        self.assertIn('Your order has been delivered', email.body)