from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_normalize_timestamps'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='contact_orbit_image',
            field=models.ImageField(blank=True, help_text='Optional image that replaces the text mark in the contact orbit.', upload_to='branding/'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='contact_orbit_mark',
            field=models.CharField(blank=True, default='S', help_text='Displayed in the contact orbit when no image is uploaded.', max_length=24),
        ),
    ]