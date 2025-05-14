import requests
from django.conf import settings


def send_telegram_notification(order):
    items = "\n".join(
        f"• {item.flower.name} - {item.quantity} шт. × {item.price} руб."
        for item in order.orderitem_set.all()
    )

    message = (
        f"🚚 *Новый заказ #{order.id}*\n"
        f"👤 Клиент: {order.user.email}\n"
        f"📅 Дата доставки: {order.delivery_date} {order.delivery_time}\n"
        f"🏠 Адрес: {order.delivery_address}\n"
        f"📱 Телефон: {order.phone}\n"
        f"💐 Состав заказа:\n{items}\n"
        f"💵 Сумма: {order.total_price} руб."
    )

    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            'chat_id': settings.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
    )
    return response.json()