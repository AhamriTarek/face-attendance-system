from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_student_raw_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='professor',
            name='nb_semaines',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='professor',
            name='date_debut',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='professor',
            name='date_fin',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='professor',
            name='seances_semaine',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
