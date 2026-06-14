from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_alter_attendancesession_end_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbsenceLevelRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(unique=True)),
                ('label', models.CharField(max_length=50)),
                ('threshold_hours', models.FloatField()),
                ('message', models.TextField()),
                ('color', models.CharField(default='yellow', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'absence_level_rules',
                'ordering': ['level'],
            },
        ),
    ]
