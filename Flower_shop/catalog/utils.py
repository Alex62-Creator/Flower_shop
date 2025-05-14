from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests
from .config import TOKEN, CHAT_ID

def send_order_email(order):
    subject = f'Подтверждение заказа №{order.id}'
    html_message = render_to_string('emails/order_created.html', {'order': order})
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        None,  # Используется DEFAULT_FROM_EMAIL
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_status_email(new_status, order):
    try:
        if not order.user.email:
            return False

        subject = f"Статус вашего заказа №{order.id} изменен"
        context = {
            'order': order,
            'new_status': new_status,
            'status_display': order.get_status_display()
        }

        # HTML версия
        html_message = render_to_string('emails/status_change.html', context)

        # Текстовая версия
        plain_message = f"""
        Здравствуйте, {order.user.first_name}!
        Статус вашего заказа №{order.id} изменен на: {new_status}
        Детали заказа:
        - Адрес доставки: {order.delivery_address}
        - Дата доставки: {order.delivery_date}
        - Сумма: {order.total_price} руб.
        """

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {str(e)}")
        return False

def send_telegram_notification(order):
    token = TOKEN
    chat_id = CHAT_ID

    # Формируем блок с товарами
    items_text = "\n".join(
        [f"• {item.flower.name} - {item.quantity} шт. x {item.price} руб. = {item.quantity * item.price} руб."
         for item in order.orderitem_set.all()]
    )

    # Полное сообщение
    message = (
        f"🛒 *Новый заказ №{order.id}*\n"
        f"👤 Клиент: {order.user.get_full_name()}\n"
        f"📞 Телефон: `{order.phone}`\n"
        f"📍 Адрес доставки: {order.delivery_address}\n"
        f"📅 Дата доставки: {order.delivery_date.strftime('%d.%m.%Y')}\n"
        f"🕒 Время доставки: {order.delivery_time}\n\n"
        f"📦 *Состав заказа:*\n{items_text}\n\n"
        f"💵 Итого: *{order.total_price} руб.*"
    )

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    })