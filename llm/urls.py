
from django.contrib import admin
from django.urls import path, include
from llm import views

app_name = 'llm'

urlpatterns = [
    path('', views.empty_llm, name='llm-analisi'),
    path('/unload/<str:llm_name>', views.unload_llm, name='llm-unload'),
    path('/load/<str:llm_name>', views.load_llm, name='llm-load'),
    path('<int:articolo_id>', views.llm_elaborazione, name='llm-elaborazione'),
]

