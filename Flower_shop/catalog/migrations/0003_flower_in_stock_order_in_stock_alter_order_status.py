# Generated by Django 5.2 on 2025-05-13 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_order_orderitem_order_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='flower',
            name='in_stock',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='order',
            name='in_stock',
            field=models.BooleanField(default=True, verbose_name='В наличии'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачен'), ('delivered', 'Доставлен'), ('canceled', 'Отменен')], default='pending', max_length=20),
        ),
    ]
