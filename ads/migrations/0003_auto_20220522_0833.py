# Generated by Django 3.2.5 on 2022-05-22 06:33

from django.conf import settings
from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0004_auto_20220522_0833'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ads', '0002_fav'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='favorites',
            field=models.ManyToManyField(related_name='favorite_ads', through='ads.Fav', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ad',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
