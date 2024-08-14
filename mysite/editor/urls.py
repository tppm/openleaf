from django.urls import path
from . import views

urlpatterns = [
    path('', views.editor_view, name='editor'),
    path('compile/', views.compile_latex, name='compile_latex'),
]