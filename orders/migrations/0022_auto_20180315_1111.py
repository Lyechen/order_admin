# Generated by Django 2.0 on 2018-03-15 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0021_auto_20180315_0910'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='min_buy',
            field=models.IntegerField(default=0, help_text='起购量', verbose_name='起购量'),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='product_place',
            field=models.CharField(blank=True, default='', help_text='产地', max_length=100, null=True, verbose_name='产地'),
        ),
    ]