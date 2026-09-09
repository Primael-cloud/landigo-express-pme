# Guide de Déploiement Cloud & Configuration du Domaine landigo-express.com

Ce guide vous explique comment mettre en ligne votre plateforme **Landigo Express** dès aujourd'hui sur le Cloud, puis comment la lier à votre nom de domaine personnalisé **`landigo-express.com`** une fois acheté.

---

## ÉTAPE 1 : Déployer Gratuitement sur Render.com (Aujourd'hui)

Vous pouvez déployer votre application immédiatement sans dépenser un centime. Render vous fournira un lien temporaire sécurisé HTTPS (ex: `https://landigo-express.onrender.com`).

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
