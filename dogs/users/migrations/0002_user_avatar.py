# Generated by Django 5.1.4 on 2025-05-23 02:30

import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to=users.models.user_avatar_path, verbose_name='Аватар'),
        ),
    ]
