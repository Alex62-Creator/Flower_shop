from django.contrib import admin, messages
from .models import Flower, Category, Order, OrderItem

# Register your models here.
admin.site.register(Flower)
admin.site.register(Category)


from django.utils.html import format_html
from django.utils.formats import date_format
from .utils import send_status_email


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'status_badge',
        'delivery_address_short',
        'phone',
        'delivery_datetime',
        'total_price',
        'created_at_formatted'
    )
    list_filter = ('status', 'created_at', 'delivery_date')
    list_editable = ('status',)
    actions = ['mark_as_paid', 'mark_as_delivered']
    search_fields = ('phone', 'delivery_address', 'user__email')

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status', 'total_price')
        }),
        ('Детали доставки', {
            'fields': ('delivery_address', 'phone', 'delivery_date', 'delivery_time')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )

    readonly_fields = ('created_at',)

    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'paid': 'warning',
            'delivered': 'success',
            'canceled': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors[obj.status],
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'

    def delivery_address_short(self, obj):
        return obj.delivery_address[:50] + '...' if len(obj.delivery_address) > 50 else obj.delivery_address

    delivery_address_short.short_description = 'Адрес'

    def delivery_datetime(self, obj):
        return format_html(
            '{}<br><small>{}</small>',
            date_format(obj.delivery_date, "d E Y"),
            obj.delivery_time.strftime("%H:%M")
        )

    delivery_datetime.short_description = 'Дата/время доставки'

    def created_at_formatted(self, obj):
        return date_format(obj.created_at, "d E Y H:i")

    created_at_formatted.short_description = 'Создан'

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:  # Если объект редактируется (не создается)
            old_status = Order.objects.get(pk=obj.pk).status  # Старый статус

        super().save_model(request, obj, form, change)

        # Если статус изменился
        if change and old_status != obj.status:
            send_status_email(new_status=obj.get_status_display(), order=obj)





@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'flower', 'quantity', 'price', 'total_price')
    search_fields = ('order__id', 'flower__name')

    def total_price(self, obj):
        return f"{obj.quantity * obj.price} руб."

    total_price.short_description = 'Сумма'