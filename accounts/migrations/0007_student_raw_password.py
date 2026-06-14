from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_rename_fullname_to_nom_add_prenom'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='raw_password',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
