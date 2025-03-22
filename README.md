# Telegram Notifier

Application Flask qui permet de recevoir des notifications Telegram pour les réunions Zoom.

## Configuration

1. Créez un fichier `.env` avec les variables suivantes :
```
TELEGRAM_BOT_TOKEN=votre_token_bot
TELEGRAM_CHAT_ID=votre_chat_id
ZOOM_API_KEY=votre_api_key
ZOOM_API_SECRET=votre_api_secret
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
python app.py
```

## Déploiement

Cette application est configurée pour être déployée sur Render.com 