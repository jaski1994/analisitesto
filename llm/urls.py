
from django.contrib import admin
from django.urls import path, include
from llm import views

app_name = 'llm'

urlpatterns = [
    path('', views.empty_llm, name='llm-analisi'),
    path('/unload/<str:llm_name>', views.unload_llm, name='llm-unload'),
    path('/load/<str:llm_name>', views.load_llm, name='llm-load'),
    path('/pull/<str:llm_name>', views.pull_llm, name='llm-pull'),
    path('<int:articolo_id>', views.llm_elaborazione, name='llm-elaborazione'),
    path('classify/', views.empty_classificazione_llm, name='llm-classify'),
    path('rag/', views.document_rag, name='llm-rag'),
    path('rag-process/', views.rag_correct, name='llm-rag-process'),
    path('ragDoc/', views.rag_elaborazione, name='llm-ragDoc'),
]

