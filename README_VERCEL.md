# Guide de Déploiement Vercel & Association du Domaine landigo-express.com

Ce guide vous explique la méthode exacte pour déployer votre plateforme **Landigo Express** sur **Vercel** en moins de 3 minutes et y ajouter plus tard votre nom de domaine **`landigo-express.com`**.

---

## ÉTAPE 1 : Déployer l'Application sur Vercel (Gratuit)

### Méthode 1 : Via l'Interface Web Vercel (Recommandée)
1. Rendez-vous sur [Vercel.com](https://vercel.com) et connectez-vous avec votre compte **GitHub**.
2. Glissez-déposez le dossier de votre projet `landigo-pme` sur votre compte **GitHub** (créez un nouveau dépôt public ou privé nommé `landigo-express`).
3. Sur Vercel, cliquez sur **"Add New..."** -> **"Project"**.
4. Importez votre dépôt GitHub `landigo-express`.
5. Dans la section **Environment Variables**, ajoutez les clés (optionnel au début) :
   - `ADMIN_USERNAME` = `admin`
   - `ADMIN_PASSWORD` = `landigo2026!`
   - `DOMAIN_NAME` = `https://landigo-express.com`
6. Cliquez sur **Deploy**.

> 🎉 Vercel déploie votre site et vous donne immédiatement un lien sécurisé HTTPS du type `https://landigo-express.vercel.app`.

---

## ÉTAPE 2 : Associer votre Domaine `landigo-express.com` sur Vercel

Lorsque vous aurez acheté votre nom de domaine **`landigo-express.com`** (chez Hostinger, LWS, Namecheap, GoDaddy, etc.) :

1. Sur le tableau de bord Vercel, ouvrez votre projet **landigo-express**.
2. Allez dans **Settings** -> **Domains**.
3. Saisissez **`landigo-express.com`** et cliquez sur **Add**.
4. Vercel vous donnera deux instructions DNS simples :
   - Pour le domaine principal (`landigo-express.com`) : Ajouter un enregistrement **A** vers l'IP `76.76.21.21` chez votre registrar.
   - Pour le sous-domaine (`www.landigo-express.com`) : Ajouter un enregistrement **CNAME** vers `cname.vercel-dns.com`.
5. Chez votre registrar, ajoutez ces 2 lignes dans la zone DNS.

Vercel générera automatiquement le certificat SSL **HTTPS** sécurisé pour **`https://landigo-express.com`** en quelques minutes !
