# Configuration Supabase

## 1. Créer la table

Dans Supabase, ouvrez **SQL Editor**, collez le contenu de `supabase_schema.sql`, puis cliquez sur **Run**. La table `orders` apparaîtra ensuite dans **Table Editor**.

## 2. Ajouter les variables d'environnement

Dans Vercel, ouvrez **Settings > Environment Variables** et ajoutez :

- `SUPABASE_URL` : URL du projet Supabase
- `SUPABASE_SERVICE_ROLE_KEY` : clé `service_role` du projet Supabase

Utilisez la clé `service_role` uniquement côté serveur. Ne la mettez jamais dans le HTML ou dans une variable `NEXT_PUBLIC_`.

Pour un lancement local, les mêmes variables peuvent être ajoutées dans un fichier `.env` à la racine du projet. Ce fichier ne doit pas être envoyé sur GitHub.

## 3. Redéployer

Après l'ajout des variables, relancez un déploiement Vercel. `server.py` utilise Supabase automatiquement quand les deux variables sont présentes; sinon il conserve SQLite comme fallback local.
