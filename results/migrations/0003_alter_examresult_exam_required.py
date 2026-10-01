import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0002_exam_alter_examresult_work_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examresult',
            name='exam',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='results',
                to='results.exam',
                verbose_name='İmtahan',
            ),
        ),
    ]
