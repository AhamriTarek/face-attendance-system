from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0004_absence_level_rules'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancesession',
            name='seance_number',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
