# Generated by Django 5.1.2 on 2025-02-24 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0003_inventario_fecha_ingreso_inventario_stock_minimo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='es_personalizado',
            field=models.BooleanField(default=False, verbose_name='Personalizado'),
        ),
    ]
