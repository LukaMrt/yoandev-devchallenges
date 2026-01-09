from django.urls import path
from . import views

# app_name permet de namespaces les URLs (ex: 'capsule:save')
app_name = 'capsule'

urlpatterns = [
    # Route pour sauvegarder un message
    path('save/', views.save_message, name='save'),

    # Route pour lire un message (avec ID)
    path('read/<int:message_id>/', views.read_message, name='read'),

    # Route pour afficher le formulaire de création
    path('', views.index, name='index'),
]
