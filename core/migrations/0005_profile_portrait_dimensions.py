import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_activitylog_options_alter_section_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='portrait_height',
            field=models.PositiveSmallIntegerField(
                default=250,
                validators=[
                    django.core.validators.MinValueValidator(170),
                    django.core.validators.MaxValueValidator(250),
                ],
                verbose_name='Homepage portrait height (px)',
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='portrait_width',
            field=models.PositiveSmallIntegerField(
                default=220,
                validators=[
                    django.core.validators.MinValueValidator(130),
                    django.core.validators.MaxValueValidator(240),
                ],
                verbose_name='Homepage portrait width (px)',
            ),
        ),
    ]