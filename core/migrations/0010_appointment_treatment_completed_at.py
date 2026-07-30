from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0009_profile_notifications_enabled')]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='treatment',
            field=models.TextField(blank=True),
        ),
    ]
