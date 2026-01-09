import json
import os
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

# Chemin vers le dossier de stockage des messages
DATA_DIR = os.path.join(settings.BASE_DIR, 'data')


def index(request):
    """
    Vue d'accueil : affiche un formulaire pour créer une capsule temporelle
    et la liste de toutes les capsules existantes
    """
    # Récupérer tous les fichiers de messages
    capsules = []

    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.startswith('message_') and filename.endswith('.json'):
                file_path = os.path.join(DATA_DIR, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Parser la date de déverrouillage
                    unlock_date = datetime.fromisoformat(data['unlock_date'])

                    # Rendre la date aware si nécessaire
                    if unlock_date.tzinfo is None:
                        unlock_date = timezone.make_aware(unlock_date)

                    # Vérifier si la capsule est déverrouillable
                    now = timezone.now()
                    is_unlocked = now >= unlock_date

                    # Calculer le temps restant si verrouillée
                    if not is_unlocked:
                        time_remaining = unlock_date - now
                        days_remaining = time_remaining.days
                        hours_remaining = time_remaining.seconds // 3600
                    else:
                        days_remaining = 0
                        hours_remaining = 0

                    capsules.append({
                        'id': data['id'],
                        'message': data['message'] if is_unlocked else '🔒 Verrouillé',
                        'unlock_date': unlock_date,
                        'created_at': data.get('created_at', 'N/A'),
                        'is_unlocked': is_unlocked,
                        'days_remaining': days_remaining,
                        'hours_remaining': hours_remaining
                    })

                except Exception as e:
                    print(f"Erreur lors du chargement de {filename}: {e}")

    # Trier par date de déverrouillage (plus proche en premier)
    capsules.sort(key=lambda x: x['unlock_date'])

    return render(request, 'capsule/index.html', {'capsules': capsules})


@csrf_exempt  # Pour simplifier, on désactive la protection CSRF (à ne pas faire en production !)
def save_message(request):
    """
    Vue pour sauvegarder un message avec une date de déverrouillage
    Accepte les requêtes POST avec 'message' et 'unlock_date'
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        # Récupérer les données du formulaire
        message = request.POST.get('message')
        unlock_date_str = request.POST.get('unlock_date')

        if not message or not unlock_date_str:
            return JsonResponse({'error': 'Message et date requis'}, status=400)

        # Parser la date (format ISO: YYYY-MM-DD)
        unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')

        # Générer un ID unique pour ce message
        message_id = int(datetime.now().timestamp() * 1000)  # Timestamp en millisecondes

        # Préparer les données à sauvegarder
        data = {
            'id': message_id,
            'message': message,
            'unlock_date': unlock_date.isoformat(),
            'created_at': datetime.now().isoformat()
        }

        # Créer le dossier data s'il n'existe pas
        os.makedirs(DATA_DIR, exist_ok=True)

        # Sauvegarder dans un fichier JSON
        file_path = os.path.join(DATA_DIR, f'message_{message_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return JsonResponse({
            'success': True,
            'message_id': message_id,
            'unlock_date': unlock_date_str
        })

    except ValueError as e:
        return JsonResponse({'error': f'Format de date invalide: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)


def read_message(request, message_id):
    """
    Vue pour lire un message uniquement si la date de déverrouillage est passée

    TODO: Vous allez implémenter la logique de validation ici !

    Cette fonction doit :
    1. Charger le fichier JSON correspondant à message_id
    2. Vérifier si la date actuelle >= unlock_date
    3. Si oui : retourner le message
    4. Si non : retourner une erreur avec le temps restant
    """
    try:
        # Construire le chemin du fichier
        file_path = os.path.join(DATA_DIR, f'message_{message_id}.json')

        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'Message non trouvé'}, status=404)

        # Charger les données
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parser la date de déverrouillage (format ISO string)
        unlock_date = datetime.fromisoformat(data['unlock_date'])

        # Rendre la date aware (avec fuseau horaire) si elle ne l'est pas
        if unlock_date.tzinfo is None:
            unlock_date = timezone.make_aware(unlock_date)

        # Obtenir la date/heure actuelle avec fuseau horaire
        now = timezone.now()

        # Vérifier si la capsule peut être déverrouillée
        if now >= unlock_date:
            # La date est passée, on peut révéler le message
            return JsonResponse({
                'success': True,
                'message': data['message'],
                'unlock_date': data['unlock_date'],
                'created_at': data.get('created_at', 'N/A')
            })
        else:
            # La capsule est encore verrouillée
            time_remaining = unlock_date - now
            days_remaining = time_remaining.days
            hours_remaining = time_remaining.seconds // 3600

            return JsonResponse({
                'error': 'Cette capsule est encore verrouillée ! Revenez plus tard.',
                'unlock_date': data['unlock_date'],
                'days_remaining': days_remaining,
                'hours_remaining': hours_remaining,
                'message': '🔒 Contenu verrouillé'
            }, status=403)

    except Exception as e:
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)
