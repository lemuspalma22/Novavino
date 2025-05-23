# Generated by Django 5.1.2 on 2025-04-18 21:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0005_producto_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='AliasProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(max_length=200, unique=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='inventario.producto')),
            ],
        ),
    ]
