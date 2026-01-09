# Django - Fonctionnement Complet

## Table des matières
1. [Architecture globale](#architecture-globale)
2. [Flux d'exécution d'une requête HTTP](#flux-dexécution-dune-requête-http)
3. [Les composants principaux](#les-composants-principaux)
4. [Le système de configuration](#le-système-de-configuration)
5. [Le système de routing (URLs)](#le-système-de-routing-urls)
6. [Les vues (Views)](#les-vues-views)
7. [Les templates](#les-templates)
8. [Les modèles (ORM)](#les-modèles-orm)
9. [Le middleware](#le-middleware)
10. [Diagramme complet](#diagramme-complet)

---

## Architecture globale

Django suit le pattern **MTV** (Model-Template-View), qui est une variante du MVC :

```
┌────────────────────────────────────────────┐
│              PROJET DJANGO                 │
│                                            │
│  ┌────────────┐  ┌────────────┐            │
│  │  settings  │  │   urls.py  │            │
│  │    .py     │  │  (routing) │            │
│  └────────────┘  └────────────┘            │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │      APPLICATIONS                    │  │
│  │                                      │  │
│  │  ┌─────────┐  ┌──────────┐           │  │
│  │  │ Models  │  │  Views   │           │  │
│  │  │  (DB)   │→ │ (Logique)│           │  │
│  │  └─────────┘  └──────────┘           │  │
│  │                    ↓                 │  │
│  │              ┌──────────┐            │  │
│  │              │Templates │            │  │
│  │              │  (HTML)  │            │  │
│  │              └──────────┘            │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### Différence Projet vs Application

**PROJET** = Conteneur global, configuration
- Un seul par site web
- Contient settings.py, urls.py principal, wsgi.py
- Configure la base de données, le fuseau horaire, etc.

**APPLICATION** = Module fonctionnel réutilisable
- Plusieurs par projet
- Chaque app a ses propres models, views, urls, templates
- Exemple : blog, forum, boutique, capsule...

---

## Flux d'exécution d'une requête HTTP

Voici exactement ce qui se passe quand un utilisateur visite `http://localhost:8000/capsule/save/` :

```
┌──────────────────────────────────────────────────────────────┐
│ 1. REQUÊTE HTTP                                              │
│    GET /capsule/save/                                        │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. manage.py / WSGI                                          │
│    - Point d'entrée de l'application                         │
│    - Charge DJANGO_SETTINGS_MODULE                           │
│    - Initialise l'application Django                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. MIDDLEWARE (requête entrante)                             │
│    Chaque middleware traite la requête dans l'ordre :        │
│    ┌────────────────────────────────────────────┐           │
│    │ SecurityMiddleware                         │           │
│    │ SessionMiddleware      ┐                   │           │
│    │ CommonMiddleware       │ Traitement         │           │
│    │ CsrfViewMiddleware     │ séquentiel         │           │
│    │ AuthenticationMiddleware│                   │           │
│    │ MessageMiddleware      │                   │           │
│    │ ClickjackingMiddleware ┘                   │           │
│    └────────────────────────────────────────────┘           │
│                                                              │
│    Chaque middleware peut :                                  │
│    - Modifier la requête                                     │
│    - Retourner une réponse (court-circuiter)                │
│    - Passer au suivant                                       │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. URL DISPATCHER (ROOT_URLCONF)                             │
│    Fichier : temporal_capsule/urls.py                        │
│                                                              │
│    urlpatterns = [                                           │
│        path('admin/', admin.site.urls),                      │
│        path('capsule/', include('capsule.urls')),  ← MATCH ! │
│    ]                                                         │
│                                                              │
│    Django parcourt urlpatterns dans l'ordre :                │
│    1. 'admin/' ? Non                                         │
│    2. 'capsule/' ? OUI !                                     │
│       → Délègue à capsule/urls.py                            │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. URL DISPATCHER (Application)                              │
│    Fichier : capsule/urls.py                                 │
│                                                              │
│    Il reste à matcher : 'save/' (car 'capsule/' déjà consommé)│
│                                                              │
│    urlpatterns = [                                           │
│        path('', views.index, name='index'),                  │
│        path('save/', views.save_message, name='save'), ← MATCH!│
│        path('read/<int:message_id>/', views.read_message),   │
│    ]                                                         │
│                                                              │
│    → Vue trouvée : views.save_message                        │
│    → Paramètres URL extraits : {} (aucun paramètre)          │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. VUE (View Function)                                       │
│    Fichier : capsule/views.py                                │
│                                                              │
│    def save_message(request):                                │
│        # request contient TOUTES les infos :                 │
│        # - request.method = 'POST'                           │
│        # - request.POST = {'message': '...', 'unlock_date': '...'} │
│        # - request.GET = {}                                  │
│        # - request.user (si authentifié)                     │
│        # - request.session                                   │
│        # - request.COOKIES                                   │
│        # - request.META (headers HTTP)                       │
│                                                              │
│        # 1. Validation des données                           │
│        message = request.POST.get('message')                 │
│        unlock_date_str = request.POST.get('unlock_date')     │
│                                                              │
│        # 2. Logique métier                                   │
│        unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')│
│        message_id = int(datetime.now().timestamp() * 1000)   │
│                                                              │
│        # 3. Sauvegarde (fichier JSON dans notre cas)         │
│        data = {'id': message_id, 'message': message, ...}    │
│        with open(file_path, 'w') as f:                       │
│            json.dump(data, f)                                │
│                                                              │
│        # 4. Retourner une réponse                            │
│        return JsonResponse({'success': True, ...})           │
│                                                              │
│    La vue DOIT retourner un objet HttpResponse (ou sous-classe)│
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. RENDU DE LA RÉPONSE                                       │
│                                                              │
│    Si c'est un template :                                    │
│    ┌──────────────────────────────────────────┐             │
│    │ render(request, 'capsule/index.html',    │             │
│    │        {'capsules': capsules})           │             │
│    │                                          │             │
│    │ 1. Django cherche le template :          │             │
│    │    capsule/templates/capsule/index.html  │             │
│    │                                          │             │
│    │ 2. Compile le template                   │             │
│    │    - Parse les {{ variables }}           │             │
│    │    - Execute les {% tags %}              │             │
│    │    - Applique les |filtres               │             │
│    │                                          │             │
│    │ 3. Génère le HTML final                  │             │
│    └──────────────────────────────────────────┘             │
│                                                              │
│    Si c'est du JSON :                                        │
│    ┌──────────────────────────────────────────┐             │
│    │ JsonResponse({'success': True})          │             │
│    │ → Sérialise en JSON                      │             │
│    │ → Ajoute header Content-Type: application/json│        │
│    └──────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. MIDDLEWARE (réponse sortante)                             │
│    Les middlewares traitent la réponse en ORDRE INVERSE :    │
│    ┌────────────────────────────────────────────┐           │
│    │ ClickjackingMiddleware ┐                   │           │
│    │ MessageMiddleware      │                   │           │
│    │ AuthenticationMiddleware│ Traitement        │           │
│    │ CsrfViewMiddleware     │ inverse           │           │
│    │ CommonMiddleware       │                   │           │
│    │ SessionMiddleware      │                   │           │
│    │ SecurityMiddleware     ┘                   │           │
│    └────────────────────────────────────────────┘           │
│                                                              │
│    Chaque middleware peut :                                  │
│    - Modifier la réponse (headers, cookies...)               │
│    - Logger, analyser, etc.                                  │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 9. RÉPONSE HTTP                                              │
│    HTTP/1.1 200 OK                                           │
│    Content-Type: application/json                            │
│    Content-Length: 75                                        │
│                                                              │
│    {"success": true, "message_id": 1767962115608, ...}       │
└──────────────────────────────────────────────────────────────┘
```

---

## Les composants principaux

### 1. manage.py - Le point d'entrée

```python
#!/usr/bin/env python
import os
import sys

def main():
    # Définit quelle configuration utiliser
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temporal_capsule.settings')

    # Import et exécute la commande CLI
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

**Commandes disponibles :**
```bash
python manage.py runserver    # Lance le serveur de dev
python manage.py migrate       # Applique les migrations DB
python manage.py makemigrations # Crée les migrations
python manage.py shell         # Shell Python interactif
python manage.py createsuperuser # Crée un admin
python manage.py startapp nom   # Crée une nouvelle app
```

---

### 2. settings.py - Configuration centrale

```python
# temporal_capsule/settings.py

# CHEMIN DE BASE
BASE_DIR = Path(__file__).resolve().parent.parent
# → /Users/luka/.../2026-01-Temporal-capsule/

# SÉCURITÉ
SECRET_KEY = 'django-insecure-...'  # Clé pour cryptographie
DEBUG = True  # Affiche les erreurs détaillées (dev uniquement!)
ALLOWED_HOSTS = []  # Domaines autorisés en production

# APPLICATIONS INSTALLÉES
INSTALLED_APPS = [
    'django.contrib.admin',      # Interface d'administration
    'django.contrib.auth',       # Authentification
    'django.contrib.contenttypes', # Type de contenu
    'django.contrib.sessions',   # Sessions utilisateur
    'django.contrib.messages',   # Messages flash
    'django.contrib.staticfiles', # Fichiers statiques
    'capsule',  # Notre application
]

# MIDDLEWARE (ordre important !)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ROUTAGE
ROOT_URLCONF = 'temporal_capsule.urls'  # Point d'entrée du routing

# TEMPLATES
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],  # Dossiers templates globaux
    'APP_DIRS': True,  # Cherche dans app/templates/
    'OPTIONS': {
        'context_processors': [  # Variables dispo partout
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# BASE DE DONNÉES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# INTERNATIONALISATION
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True  # Internationalisation
USE_TZ = True    # Support des timezones

# FICHIERS STATIQUES
STATIC_URL = 'static/'
```

**Comment Django charge settings.py :**

```
1. manage.py définit : DJANGO_SETTINGS_MODULE = 'temporal_capsule.settings'
2. Django importe ce module Python
3. Lit toutes les variables en MAJUSCULES
4. Les stocke dans django.conf.settings
5. Accessible partout via : from django.conf import settings
```

---

### 3. urls.py - Le système de routing

#### Niveau projet (temporal_capsule/urls.py)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('capsule/', include('capsule.urls')),
]
```

**Fonctionnement de `include()` :**

```
Requête : /capsule/save/

1. Django teste 'admin/'
   → /capsule/save/ commence par 'admin/' ? NON

2. Django teste 'capsule/'
   → /capsule/save/ commence par 'capsule/' ? OUI !
   → Consomme 'capsule/' de l'URL
   → Reste à traiter : 'save/'
   → Délègue à capsule/urls.py avec 'save/'
```

#### Niveau application (capsule/urls.py)

```python
from django.urls import path
from . import views

app_name = 'capsule'  # Namespace pour reverse URLs

urlpatterns = [
    # Pattern simple
    path('', views.index, name='index'),

    # Pattern avec paramètre
    path('read/<int:message_id>/', views.read_message, name='read'),
    #           ↑              ↑
    #       type  nom du paramètre

    # Pattern POST
    path('save/', views.save_message, name='save'),
]
```

**Types de paramètres d'URL :**

```python
path('article/<int:id>/')           # Capture un entier
path('user/<str:username>/')        # Capture une chaîne
path('file/<path:filepath>/')       # Capture un chemin (avec /)
path('date/<slug:slug>/')           # Capture un slug (a-z0-9-)
path('uuid/<uuid:uuid>/')           # Capture un UUID
```

**Exemple concret :**

```
URL : /capsule/read/1767962115608/

1. Pattern testé : 'read/<int:message_id>/'
2. Regex généré : ^read/(?P<message_id>[0-9]+)/$
3. Match réussi : message_id = 1767962115608
4. Appelle : views.read_message(request, message_id=1767962115608)
```

**Reverse URL (générer une URL depuis le code) :**

```python
from django.urls import reverse

# Méthode 1 : avec namespace
url = reverse('capsule:read', kwargs={'message_id': 123})
# → '/capsule/read/123/'

# Méthode 2 : dans les templates
{% url 'capsule:read' message_id=123 %}
```

---

### 4. views.py - La logique métier

Une vue est une **fonction Python** qui :
- Reçoit un `HttpRequest`
- Retourne un `HttpResponse`

#### L'objet HttpRequest

```python
def my_view(request):
    # MÉTHODE HTTP
    request.method  # 'GET', 'POST', 'PUT', 'DELETE'...

    # DONNÉES
    request.GET     # QueryDict : ?key=value
    request.POST    # QueryDict : données formulaire
    request.body    # bytes : données brutes
    request.FILES   # Fichiers uploadés

    # UTILISATEUR
    request.user    # Utilisateur authentifié (ou AnonymousUser)

    # SESSION
    request.session # Dict-like : stockage côté serveur
    request.session['key'] = 'value'

    # COOKIES
    request.COOKIES # Dict des cookies

    # HEADERS
    request.META    # Dict des headers HTTP
    request.META['HTTP_USER_AGENT']
    request.META['REMOTE_ADDR']

    # URL
    request.path      # '/capsule/save/'
    request.get_host() # 'localhost:8000'
    request.is_secure() # True si HTTPS
```

#### Types de réponses

```python
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseForbidden,
    HttpResponseServerError
)
from django.shortcuts import render, redirect

# 1. Réponse HTML simple
def view1(request):
    return HttpResponse('<h1>Hello</h1>', content_type='text/html')

# 2. Template
def view2(request):
    context = {'name': 'John', 'items': [1, 2, 3]}
    return render(request, 'app/template.html', context)

# 3. JSON
def view3(request):
    data = {'success': True, 'message': 'OK'}
    return JsonResponse(data)

# 4. Redirection
def view4(request):
    return redirect('capsule:index')  # Par nom de route
    # ou
    return redirect('/capsule/')      # Par URL

# 5. Erreur 404
def view5(request):
    return HttpResponseNotFound('Page non trouvée')

# 6. Téléchargement de fichier
def view6(request):
    with open('file.pdf', 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="file.pdf"'
        return response
```

#### Décorateurs utiles

```python
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Limiter aux méthodes HTTP
@require_http_methods(["GET", "POST"])
def view1(request):
    pass

@require_POST
def view2(request):
    pass

# Désactiver CSRF (attention !)
@csrf_exempt
def view3(request):
    pass

# Requiert authentification
@login_required
def view4(request):
    # request.user est forcément authentifié
    pass
```

---

### 5. Templates - Le moteur de rendu

#### Localisation des templates

```
capsule/
├── templates/
│   └── capsule/        ← Namespace de l'app
│       ├── index.html
│       └── detail.html
```

**Pourquoi `capsule/templates/capsule/` (doublon) ?**

```
Si deux apps ont un fichier index.html :
- blog/templates/index.html
- capsule/templates/index.html

Django cherche dans TOUS les dossiers templates/.
Sans namespace, il prendrait le premier trouvé !

Avec namespace :
- blog/templates/blog/index.html
- capsule/templates/capsule/index.html

render(request, 'capsule/index.html')  ← Pas d'ambiguïté !
```

#### Syntaxe du template

```django
{# Ceci est un commentaire #}

{# 1. VARIABLES #}
{{ variable }}
{{ user.username }}
{{ items.0 }}          {# Premier élément #}
{{ dict.key }}

{# 2. FILTRES #}
{{ name|lower }}                {# Minuscules #}
{{ date|date:"d/m/Y" }}         {# Format date #}
{{ text|truncatewords:30 }}     {# Tronquer #}
{{ count|pluralize }}           {# Ajoute 's' si > 1 #}
{{ value|default:"N/A" }}       {# Valeur par défaut #}
{{ html|safe }}                 {# Pas d'échappement #}

{# 3. TAGS #}

{# Conditions #}
{% if user.is_authenticated %}
    Bonjour {{ user.username }}
{% elif user.is_anonymous %}
    Veuillez vous connecter
{% else %}
    Erreur
{% endif %}

{# Boucles #}
{% for item in items %}
    {{ forloop.counter }}. {{ item }}

    {# Variables dans les boucles : #}
    {# forloop.counter   : 1, 2, 3... #}
    {# forloop.counter0  : 0, 1, 2... #}
    {# forloop.first     : True si premier #}
    {# forloop.last      : True si dernier #}
{% empty %}
    Aucun élément
{% endfor %}

{# Inclusion #}
{% include 'capsule/partial.html' %}

{# URLs #}
<a href="{% url 'capsule:read' message_id=123 %}">Lire</a>

{# Fichiers statiques #}
{% load static %}
<img src="{% static 'images/logo.png' %}">

{# Héritage de templates #}
{# base.html #}
<!DOCTYPE html>
<html>
<head>
    {% block title %}Mon Site{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>

{# page.html #}
{% extends 'base.html' %}

{% block title %}Ma Page{% endblock %}

{% block content %}
    <h1>Contenu de la page</h1>
{% endblock %}
```

#### Context processors

Variables automatiquement disponibles dans TOUS les templates :

```python
# settings.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',  # → request
            'django.contrib.auth.context_processors.auth', # → user, perms
            'django.contrib.messages.context_processors.messages', # → messages
        ],
    },
}]
```

Dans n'importe quel template :
```django
{{ request.path }}
{{ user.username }}
{{ user.is_authenticated }}
```

---

### 6. Models - L'ORM Django

**ORM** = Object-Relational Mapping = Mapper des objets Python ↔ Tables SQL

Notre projet n'utilise pas de modèles (stockage JSON), mais voici comment ça marche :

#### Définir un modèle

```python
# capsule/models.py
from django.db import models
from django.utils import timezone

class Capsule(models.Model):
    """
    Chaque classe = une table SQL
    Chaque attribut = une colonne
    """

    # Colonnes
    message = models.TextField()
    unlock_date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    # Métadonnées
    class Meta:
        ordering = ['unlock_date']  # Tri par défaut
        verbose_name = 'Capsule temporelle'
        verbose_name_plural = 'Capsules temporelles'

    # Méthode affichage
    def __str__(self):
        return f"Capsule {self.id} - {self.unlock_date}"

    # Méthodes custom
    def is_unlocked(self):
        return timezone.now() >= self.unlock_date
```

**SQL généré automatiquement :**

```sql
CREATE TABLE capsule_capsule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    unlock_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL
);
```

#### Utiliser les modèles

```python
from capsule.models import Capsule
from django.utils import timezone

# CRÉER
capsule = Capsule(
    message="Secret",
    unlock_date=timezone.now() + timedelta(days=30)
)
capsule.save()  # INSERT INTO...

# ou en une ligne
capsule = Capsule.objects.create(message="Secret", unlock_date=...)

# LIRE
all_capsules = Capsule.objects.all()  # SELECT * FROM capsule_capsule
capsule = Capsule.objects.get(id=1)   # SELECT ... WHERE id=1

# Filtrer
locked = Capsule.objects.filter(unlock_date__gt=timezone.now())
# SELECT ... WHERE unlock_date > NOW()

unlocked = Capsule.objects.filter(unlock_date__lte=timezone.now())
# SELECT ... WHERE unlock_date <= NOW()

# MODIFIER
capsule = Capsule.objects.get(id=1)
capsule.message = "Nouveau message"
capsule.save()  # UPDATE capsule_capsule SET message=... WHERE id=1

# SUPPRIMER
capsule.delete()  # DELETE FROM capsule_capsule WHERE id=1

# Compter
count = Capsule.objects.count()  # SELECT COUNT(*) ...

# Exister
exists = Capsule.objects.filter(id=1).exists()  # SELECT 1 ... LIMIT 1

# Premier/Dernier
first = Capsule.objects.first()
last = Capsule.objects.last()

# Trier
by_date = Capsule.objects.order_by('unlock_date')
by_date_desc = Capsule.objects.order_by('-unlock_date')  # DESC
```

#### Relations

```python
class Author(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    # ↑ Clé étrangère : un livre → un auteur

# Utilisation
author = Author.objects.create(name="Victor Hugo")
book = Book.objects.create(title="Les Misérables", author=author)

# Requête inverse
books = author.book_set.all()  # Tous les livres de cet auteur
```

#### Migrations

Quand vous modifiez un modèle :

```bash
# 1. Créer un fichier de migration
python manage.py makemigrations
# → capsule/migrations/0001_initial.py

# 2. Appliquer les migrations
python manage.py migrate
# → Exécute les commandes SQL
```

---

### 7. Le Middleware

Middleware = Couche qui traite TOUTES les requêtes/réponses avant/après les vues.

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # 1
    'django.contrib.sessions.middleware.SessionMiddleware', # 2
    'django.middleware.common.CommonMiddleware',          # 3
    'django.middleware.csrf.CsrfViewMiddleware',          # 4
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 5
    'django.contrib.messages.middleware.MessageMiddleware', # 6
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # 7
]
```

**Flux d'exécution :**

```
Requête
  ↓
[1] SecurityMiddleware       ┐
[2] SessionMiddleware        │
[3] CommonMiddleware         │ Ordre d'entrée
[4] CsrfViewMiddleware       │
[5] AuthenticationMiddleware │
[6] MessageMiddleware        │
[7] ClickjackingMiddleware   ┘
  ↓
VUE (views.py)
  ↓
[7] ClickjackingMiddleware   ┐
[6] MessageMiddleware        │
[5] AuthenticationMiddleware │ Ordre inverse
[4] CsrfViewMiddleware       │
[3] CommonMiddleware         │
[2] SessionMiddleware        │
[1] SecurityMiddleware       ┘
  ↓
Réponse
```

**Rôle de chaque middleware :**

1. **SecurityMiddleware** : Ajoute headers de sécurité (HSTS, etc.)
2. **SessionMiddleware** : Gère les sessions utilisateur (cookies)
3. **CommonMiddleware** : Normalise les URLs, gère les ETags
4. **CsrfViewMiddleware** : Protection contre CSRF (POST)
5. **AuthenticationMiddleware** : Ajoute `request.user`
6. **MessageMiddleware** : Messages flash (succès, erreurs)
7. **ClickjackingMiddleware** : Protection contre clickjacking (X-Frame-Options)

#### Créer son propre middleware

```python
# capsule/middleware.py
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code AVANT la vue
        print(f"Requête : {request.method} {request.path}")

        # Appeler la vue
        response = self.get_response(request)

        # Code APRÈS la vue
        print(f"Réponse : {response.status_code}")

        return response

# settings.py
MIDDLEWARE = [
    ...
    'capsule.middleware.LoggingMiddleware',
]
```

---

## Diagramme complet

```
                        ┌─────────────────────┐
                        │   NAVIGATEUR        │
                        │  HTTP Request       │
                        └──────────┬──────────┘
                                   │
                                   ↓
┌──────────────────────────────────────────────────────────────┐
│                       SERVEUR DJANGO                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ manage.py / WSGI                                       │ │
│  │ • Charge DJANGO_SETTINGS_MODULE                        │ │
│  │ • Initialise Django                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ settings.py                                            │ │
│  │ • Configuration globale                                │ │
│  │ • INSTALLED_APPS, MIDDLEWARE, DATABASES, etc.          │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MIDDLEWARE (Requête entrante)                          │ │
│  │ Security → Session → Common → CSRF → Auth → ...        │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ URL DISPATCHER                                         │ │
│  │ • temporal_capsule/urls.py (racine)                    │ │
│  │ • Trouve le pattern correspondant                      │ │
│  │ • Include vers capsule/urls.py si nécessaire           │ │
│  │ • Extrait les paramètres d'URL                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ VIEW (capsule/views.py)                                │ │
│  │ • Reçoit HttpRequest                                   │ │
│  │ • Accède aux données : POST, GET, session, user...     │ │
│  │ • Execute la logique métier                            │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────┐         │ │
│  │  │ Option A : Accès aux Models (ORM)        │         │ │
│  │  │ • Query la base de données               │         │ │
│  │  │ • CRUD operations                         │         │ │
│  │  └──────────────────────────────────────────┘         │ │
│  │                  ↓                                     │ │
│  │  ┌──────────────────────────────────────────┐         │ │
│  │  │ Option B : Autre traitement              │         │ │
│  │  │ • Fichiers JSON (notre cas)              │         │ │
│  │  │ • APIs externes                           │         │ │
│  │  │ • Calculs, etc.                          │         │ │
│  │  └──────────────────────────────────────────┘         │ │
│  │                  ↓                                     │ │
│  │ • Retourne HttpResponse                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ RENDU                                                  │ │
│  │                                                        │ │
│  │  Si render() :                                         │ │
│  │  ┌──────────────────────────────────────────┐         │ │
│  │  │ TEMPLATE ENGINE                          │         │ │
│  │  │ 1. Trouve le fichier template            │         │ │
│  │  │    app/templates/app/template.html       │         │ │
│  │  │ 2. Parse {{ variables }}, {% tags %}     │         │ │
│  │  │ 3. Remplace par les valeurs du context   │         │ │
│  │  │ 4. Génère HTML final                     │         │ │
│  │  └──────────────────────────────────────────┘         │ │
│  │                                                        │ │
│  │  Si JsonResponse() :                                   │ │
│  │  ┌──────────────────────────────────────────┐         │ │
│  │  │ JSON SERIALIZATION                       │         │ │
│  │  │ • Convertit dict → JSON string           │         │ │
│  │  │ • Ajoute Content-Type: application/json  │         │ │
│  │  └──────────────────────────────────────────┘         │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MIDDLEWARE (Réponse sortante)                          │ │
│  │ ... → Auth → CSRF → Common → Session → Security        │ │
│  │ • Modifie headers, cookies                             │ │
│  │ • Ajoute mesures de sécurité                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ↓                               │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │   HTTP Response      │
                    │   Envoyé au client   │
                    └──────────────────────┘
```

---

## Résumé des concepts clés

### 1. MTV Pattern
- **Model** : Données (ORM)
- **Template** : Présentation (HTML)
- **View** : Logique métier (Controller)

### 2. Projet vs Application
- **Projet** = Configuration globale
- **Application** = Module fonctionnel réutilisable

### 3. Flux de requête
```
HTTP → manage.py → Middleware → URL Dispatcher → View → Template → Middleware → HTTP
```

### 4. Composants essentiels
- `manage.py` : CLI
- `settings.py` : Configuration
- `urls.py` : Routing
- `views.py` : Logique
- `models.py` : Base de données
- `templates/` : HTML

### 5. Django cherche les templates ainsi
```
1. DIRS dans settings.TEMPLATES
2. app/templates/ pour chaque INSTALLED_APP (si APP_DIRS=True)
```

### 6. L'objet request contient TOUT
```python
request.method, .GET, .POST, .FILES, .user, .session, .COOKIES, .META
```

### 7. Les vues retournent TOUJOURS un HttpResponse
```python
HttpResponse, JsonResponse, render(), redirect()
```

---

## Pour aller plus loin

### Class-Based Views (CBV)
Alternative aux vues fonctions :

```python
from django.views import View
from django.views.generic import ListView, DetailView

class CapsuleListView(ListView):
    model = Capsule
    template_name = 'capsule/list.html'
    context_object_name = 'capsules'

# urls.py
path('list/', CapsuleListView.as_view(), name='list'),
```

### Django REST Framework
Pour créer des APIs REST complètes :

```python
from rest_framework import serializers, viewsets

class CapsuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capsule
        fields = '__all__'

class CapsuleViewSet(viewsets.ModelViewSet):
    queryset = Capsule.objects.all()
    serializer_class = CapsuleSerializer
```

### Signals
Déclencher du code à certains événements :

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Capsule)
def capsule_created(sender, instance, created, **kwargs):
    if created:
        print(f"Nouvelle capsule créée : {instance.id}")
```

### Admin Django
Interface d'administration automatique :

```python
# capsule/admin.py
from django.contrib import admin
from .models import Capsule

@admin.register(Capsule)
class CapsuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'unlock_date', 'is_unlocked']
    list_filter = ['unlock_date']
    search_fields = ['message']
```

---

**Voilà ! Vous comprenez maintenant le fonctionnement complet de Django. 🎉**
