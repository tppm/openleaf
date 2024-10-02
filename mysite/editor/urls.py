from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_select_view, name='project_select'),
    path('register/', views.register_view, name='register'),
    path('editor/', views.editor_view, name='editor'),
    path('editor/<int:project_id>/', views.editor_view, name='editor'),
    path('create_project/', views.create_project, name='create_project'),
]
