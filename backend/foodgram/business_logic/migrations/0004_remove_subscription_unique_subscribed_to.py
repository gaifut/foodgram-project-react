# Generated by Django 3.2.16 on 2024-02-20 16:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('business_logic', '0003_auto_20240220_1622'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscription',
            name='unique_subscribed_to',
        ),
    ]
