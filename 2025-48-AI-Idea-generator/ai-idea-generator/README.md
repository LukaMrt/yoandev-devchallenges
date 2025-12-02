# AI Idea Generator

Générateur d'idées d'activités personnalisées basé sur l'âge et les centres d'intérêts. Les idées sont générées par IA.

## Technologies

- PHP 8.5+
- Symfony 8.0
- Symfony AI Bundle
- Twig
- Docker

## Installation

### Prérequis

- Docker et Docker Compose
- Ou PHP 8.5+ avec Composer

### Avec Docker

```bash
docker-compose up -d
```

L'application sera disponible sur `http://localhost:8080`

### Sans Docker

```bash
composer install
symfony server:start
```

## Utilisation

1. Accédez à l'application
2. Renseignez les informations :
   - Modèle d'IA à utiliser
   - Clé API
   - Âge de l'utilisateur
   - Centres d'intérêts
   - Nombre d'idées souhaitées
3. Soumettez le formulaire
4. L'IA génère des idées d'activités personnalisées

## Structure

```
src/
├── Controller/      # Contrôleurs Symfony
├── DTO/            # Data Transfer Objects
├── Entity/         # Entités
└── Service/        # Services métier
```
