# Generated by Django 5.0.6 on 2024-12-11 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_pronct', '0002_cadastrofinanceiro_pago_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cadastrofinanceiro',
            name='pagante',
            field=models.TextField(default='Cliente', max_length=225),
        ),
    ]