# Generated by Django 5.0.6 on 2024-06-13 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socket_api', '0009_customuser_last_seen'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='show_last_seen',
            field=models.BooleanField(default=True),
        ),
    ]
