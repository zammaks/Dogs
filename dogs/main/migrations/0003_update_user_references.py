from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0002_delete_user'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='bookings', to='users.user', verbose_name='Владелец'),
        ),
        migrations.AlterField(
            model_name='animal',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='animals', to='users.user'),
        ),
        migrations.AlterField(
            model_name='dogsitter',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, to='users.user'),
        ),
    ] 