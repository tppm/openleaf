from django.contrib import admin
from django.utils.html import format_html
from .models import LatexProject, LatexFile, ProjectImage

class LatexFileInline(admin.TabularInline):
    model = LatexFile
    extra = 1
    fields = ('filename', 'content', 'is_main_file')

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No Image"

@admin.register(LatexProject)
class LatexProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'user__username')
    inlines = [LatexFileInline, ProjectImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

@admin.register(LatexFile)
class LatexFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'project', 'is_main_file', 'created_at', 'updated_at')
    list_filter = ('project', 'is_main_file', 'created_at', 'updated_at')
    search_fields = ('filename', 'content', 'project__title')

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'image_preview', 'caption', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('project__title', 'caption')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No Image"