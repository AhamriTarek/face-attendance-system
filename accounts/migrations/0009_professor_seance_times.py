from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_professor_planning_fields'),
    ]

    operations = [
        migrations.AddField(model_name='professor', name='heure_debut_s1', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s1',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s2', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s2',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s3', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s3',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s4', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s4',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s5', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s5',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s6', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s6',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s7', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s7',   field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_debut_s8', field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name='professor', name='heure_fin_s8',   field=models.TimeField(blank=True, null=True)),
    ]
