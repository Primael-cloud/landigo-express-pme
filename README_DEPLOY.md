# Guide de Déploiement Cloud & Configuration du Domaine landigo-express.com

Ce guide vous explique comment mettre en ligne votre plateforme **Landigo Express** dès aujourd'hui sur le Cloud, puis comment la lier à votre nom de domaine personnalisé **`landigo-express.com`** une fois acheté.


## ÉTAPE 1 : Déployer Gratuitement sur Render.com (Aujourd'hui)

Vous pouvez déployer votre application immédiatement sans dépenser un centime. Render vous fournira un lien temporaire sécurisé HTTPS (ex: `https://landigo-express.onrender.com`).

### Notifications de suivi projet

Le paiement et l'avancement du projet sont enregistrés séparément. Après 24 heures suivant la confirmation du paiement, le projet passe automatiquement à `EN_COURS` lors du prochain chargement de l'administration. Les changements vers `EN_COURS`, `LIVRE` ou `PROBLEME` déclenchent un email au client.

Pour activer l'envoi email, ajoutez ces variables d'environnement dans Render ou Vercel :

```text
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=b90af3001@smtp-brevo.com
SMTP_PASSWORD=xsmtpsib-9434f23efa60d217a328ee26f897d710f49ab737935ae96d8a46d25808618384-INtCzICiizHV3GCv
NOTIFICATION_FROM=yangbasile@gmail.com
```

Sans ces variables, le statut est bien mis à jour mais aucun email ne peut être envoyé. Le bouton WhatsApp reste disponible dans l'administration pour contacter manuellement le client.

Après avoir ajouté la table `notifications` dans `supabase_schema.sql`, l'historique est également conservé dans Supabase et reste consultable depuis l'administration après un redéploiement.

Pour envoyer automatiquement les notifications par WhatsApp lorsqu'aucun email n'est fourni, configurez aussi Meta WhatsApp Cloud API :

```text
WHATSAPP_API_VERSION=v21.0
WHATSAPP_PHONE_NUMBER_ID=votre-identifiant-de-numero-meta
WHATSAPP_ACCESS_TOKEN=votre-jeton-meta
```

Le numéro doit être au format international, par exemple `2250700000000`. Hors de la fenêtre de 24 heures, Meta exige généralement un modèle WhatsApp approuvé. Révoquez toute clé SMTP exposée dans ce fichier et remplacez-la.
### Procédure en 5 clics :
1. Créez un compte gratuit sur [Render.com](https://render.com).
2. Déposez ce dossier `landigo-pme` sur votre compte **GitHub** (ou GitLab).
3. Sur Render, cliquez sur **New +** -> **Web Service**.
4. Sélectionnez votre dépôt GitHub `landigo-pme`.
5. Render détectera automatiquement le `Dockerfile` et déploiera votre application en 2 minutes !

> 🎉 Votre plateforme sera en ligne et accessible partout dans le monde via une URL du type `https://landigo-express.onrender.com`.

---

## ÉTAPE 2 : Lier votre Domaine `landigo-express.com` (Plus tard)

Lorsque vous aurez acheté votre nom de domaine `landigo-express.com` chez votre registrar (LWS, Hostinger, Namecheap, GoDaddy...) :

1. Sur **Render.com**, allez dans les paramètres de votre Web Service -> section **Custom Domains**.
2. Cliquez sur **Add Custom Domain** et saisissez `landigo-express.com` (et `www.landigo-express.com`).
3. Render affichera deux enregistrements DNS simples :
   - Un enregistrement **CNAME** vers `landigo-express.onrender.com`
   - Un enregistrement **A** (adresse IP Render).
4. Connectez-vous sur votre espace registrar (où vous avez acheté le domaine) et collez ces deux enregistrements dans la zone DNS.

Render va générer **automatiquement et gratuitement** le certificat SSL HTTPS (`https://landigo-express.com`) !

---

## ÉTAPE 3 : Activer vos Clés CinetPay Live (Après Validation)

Dès que votre compte marchand CinetPay est approuvé :
1. Allez sur **Render.com** -> section **Environment**.
2. Modifiez la variable `CINETPAY_MODE` de `sandbox` à `live`.
3. Ajoutez `CINETPAY_SITE_ID` et `CINETPAY_API_KEY` fournis par CinetPay.
4. Cliquez sur **Save Changes**. Le site sera automatiquement à jour avec les encaissements réels !
