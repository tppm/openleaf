from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin 
from django.conf import settings
import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

def project_image_path(instance, filename):
    # Images will be uploaded to MEDIA_ROOT/latex_projects/user_<id>/<project_id>/images/<filename>
    return f'latex_projects/user_{instance.project.user.id}/{instance.project.id}/images/{filename}'

class LatexProject(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='latex_projects')

    def __str__(self):
        return self.title

class LatexFile(models.Model):
    project = models.ForeignKey(LatexProject, on_delete=models.CASCADE, related_name='latex_files')
    filename = models.CharField(max_length=255)
    content = models.TextField()
    is_main_file = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.title} - {self.filename}"

class ProjectImage(models.Model):
    project = models.ForeignKey(LatexProject, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=project_image_path)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - {self.image.name}"

    @property
    def filename(self):
        return os.path.basename(self.image.name)