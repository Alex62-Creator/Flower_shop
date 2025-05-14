from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    username = models.CharField('Пользователь', max_length=30, blank=True)
    # Обязательные поля для аутентификации
    email = models.EmailField(('Электронная почта'), unique=True, error_messages={'unique': ("Пользователь с таким email уже существует."),})
    # Дополнительные поля
    phone = models.CharField(('Телефон'), max_length=20, blank=True, null=True)
    address = models.CharField(('Адрес'), max_length=200, blank=True, null=True)

    # Настройки модели
    USERNAME_FIELD = 'email'  # Поле для входа
    REQUIRED_FIELDS = ['username']  # Поля для createsuperuser

    class Meta:
        verbose_name = ('Пользователь')
        verbose_name_plural = ('Пользователи')

    def __str__(self):
        return self.email

class Category(models.Model):
    """Модель категории цветов"""
    name = models.CharField('Название категории', max_length=100, unique=True)

    class Meta:
        verbose_name = ('Категория')
        verbose_name_plural = ('Категории')

    def __str__(self):
        return self.name

class Flower(models.Model):
    """Модель цветка"""
    name = models.CharField('Название', max_length=100)
    price = models.DecimalField('Цена', max_digits=6, decimal_places=2)
    image = models.ImageField('Изображение', upload_to='catalog/img/', default='default_flower.jpeg')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='flowers')
    in_stock = models.BooleanField(default=True)

    class Meta:
        verbose_name = ('Цветок')
        verbose_name_plural = ('Цветы')
        ordering = ['name']

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,   # Связываемая модель
        on_delete=models.CASCADE,   # Поведение при удалении
        related_name='cart'         # Имя обратной связи
    )
    created_at = models.DateTimeField(auto_now_add=True)    # Автозаполнение времени

    @property
    def total_price(self):
        return sum(
            item.flower.price * item.quantity
            for item in self.items.all()
        )

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    flower = models.ForeignKey('catalog.Flower', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.flower.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField('catalog.Flower', through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_address = models.TextField()
    phone = models.CharField(max_length=20)
    delivery_date = models.DateField(verbose_name='Дата доставки')
    delivery_time = models.TimeField(verbose_name='Время доставки')
    created_at = models.DateTimeField(auto_now_add=True)
    in_stock = models.BooleanField('В наличии', default=True)

    @property
    def total_items(self):
        return self.orderitem_set.count()

    @property
    def can_reorder(self):
        """Проверяет возможность повтора заказа"""
        return any(item.flower.in_stock for item in self.orderitem_set.all())

    @property
    def can_cancel(self):
        """Проверяет возможность отмены заказа"""
        return self.status in ['pending', 'paid']

    @property
    def status_color(self):
        return {
            'pending': 'warning',
            'paid': 'primary',
            'delivered': 'success',
            'canceled': 'danger'
        }.get(self.status, 'secondary')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    flower = models.ForeignKey('catalog.Flower', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price