from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0008_doctor_profile_details')]

    operations = [
        migrations.AddField(model_name='profile', name='notifications_enabled', field=models.BooleanField(default=True)),
    ]
