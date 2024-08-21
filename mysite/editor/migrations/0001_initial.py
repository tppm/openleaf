from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone

def create_default_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    default_user, created = User.objects.get_or_create(
        username='default',
        defaults={'password': 'defaultpassword', 'is_staff': True, 'is_superuser': True}
    )
    return default_user

def set_default_user(apps, schema_editor):
    LatexDocument = apps.get_model('editor', 'LatexDocument')
    default_user = create_default_user(apps, schema_editor)
    LatexDocument.objects.filter(user__isnull=True).update(user=default_user)

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LatexDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(set_default_user),
    ]