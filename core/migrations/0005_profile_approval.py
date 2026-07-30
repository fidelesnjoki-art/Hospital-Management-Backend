# Existing staff are intentionally made pending so they require an explicit
# super-admin review after this authorization change is deployed.
from django.db import migrations, models


def set_existing_approval_states(apps, schema_editor):
    Profile = apps.get_model('core', 'Profile')
    Profile.objects.filter(role='staff').update(
        is_approved=False,
        approval_status='pending',
    )
    Profile.objects.filter(role='patient').update(
        is_approved=True,
        approval_status='approved',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='approved',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[
                    ('patient', 'Patient'),
                    ('staff', 'Staff Admin'),
                    ('super_admin', 'Super Admin'),
                ],
                default='patient',
                max_length=20,
            ),
        ),
        migrations.RunPython(set_existing_approval_states, migrations.RunPython.noop),
    ]
