# Generated by Django 3.0.8 on 2020-10-24 01:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cfc_app', '0005_auto_20201024_0139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hash',
            name='fob_method',
            field=models.CharField(max_length=6),
        ),
        migrations.AlterField(
            model_name='hash',
            name='generated_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='hash',
            name='hashcode',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='hash',
            name='item_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='hash',
            name='size',
            field=models.PositiveIntegerField(),
        ),
    ]
