import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advisories', '0003_advisormessage_read_advisormessage_reply_count_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='recommendation',
            old_name='status',
            new_name='review_status',
        ),
        migrations.AddField(
            model_name='recommendation',
            name='review_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_recommendations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='student_acknowledged',
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            "UPDATE advisories_recommendation SET review_status = 'pending_review' WHERE review_status = 'pending'",
            migrations.RunSQL.noop,
        ),
    ]
