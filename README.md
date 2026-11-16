# Gestion commerciale — Flask + MySQL + Render

Application web en français pour gérer les catégories de produits, les produits et les ventes.

## Fonctionnalités

- Tableau de bord : nombre de catégories, produits et ventes, dernières ventes.
- Catégories : lister, ajouter, modifier et supprimer (si aucun produit n'y est rattaché).
- Produits : lister, ajouter, modifier et supprimer (si aucune vente n'y est rattachée).
- Ventes : lister, enregistrer et supprimer.
- Endpoint `/health` pour vérifier la connexion MySQL.

## 1. Préparer la base FreeDB

Dans phpMyAdmin, sélectionnez la base déjà attribuée par FreeDB (dans votre cas, elle semble s'appeler `freedb_y1cxAKhX`).

Ouvrez l'onglet SQL et exécutez le contenu de `schema.sql` si les trois tables n'existent pas encore.

Si les tables existent déjà, vérifiez que leurs colonnes correspondent à celles de `schema.sql`. Les noms de tables attendus sont exactement `categorie_produits`, `produits` et `ventes`.

**Important :** l'application ne crée pas de base de données et ne lance pas automatiquement `db.create_all()`. Elle utilise les tables existantes.

## 2. Récupérer les informations MySQL FreeDB

Dans le panneau FreeDB/phpMyAdmin ou dans les informations de connexion fournies par l'hébergeur, récupérez :
- l'hôte/serveur MySQL (hostname), pas l'URL de phpMyAdmin ;
- le port MySQL (souvent 3306, à confirmer) ;
- le nom exact de la base ;
- le nom d'utilisateur ;
- le mot de passe.

Vérifiez aussi que FreeDB autorise les connexions MySQL distantes depuis Render. Certains hébergeurs gratuits limitent les connexions externes ou exigent une autorisation IP. Si les connexions distantes sont bloquées, l'application ne pourra pas joindre cette base depuis Render : il faudra demander l'activation à FreeDB ou choisir un hébergeur MySQL accessible à distance.

## 3. Tester localement (facultatif)

Python 3.10 ou plus récent est recommandé.

```bash
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS/Linux :
source .venv/bin/activate

pip install -r requirements.txt
```

Copiez `.env.example` vers `.env`, puis renseignez les vraies valeurs. Chargez les variables d'environnement dans votre terminal avant de lancer l'application, ou utilisez un outil comme python-dotenv (non inclus ici). Pour un test rapide sous PowerShell :

```powershell
$env:MYSQL_HOST="votre_hote"
$env:MYSQL_DATABASE="votre_base"
$env:MYSQL_USER="votre_utilisateur"
$env:MYSQL_PASSWORD="votre_mot_de_passe"
$env:MYSQL_PORT="3306"
python app.py
```

Ouvrez `http://127.0.0.1:5000`.

## 4. Déployer sur Render

1. Décompressez le projet.
2. Envoyez les fichiers dans un dépôt GitHub.
3. Sur Render, choisissez **New + > Web Service** et connectez le dépôt.
4. Render détectera `render.yaml` (ou saisissez manuellement) :
   - Build command : `pip install -r requirements.txt`
   - Start command : `gunicorn app:app`
5. Dans **Environment**, ajoutez les valeurs réelles :
   - `MYSQL_HOST`
   - `MYSQL_PORT`
   - `MYSQL_DATABASE`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `SECRET_KEY` (une longue valeur aléatoire)
6. Déployez, puis ouvrez l'URL Render fournie.

Ne publiez jamais votre mot de passe MySQL dans GitHub, dans le code ou dans une capture d'écran. Les variables d'environnement Render doivent contenir les secrets.

## 5. Dépannage

- Erreur `Access denied`: identifiants incorrects ou utilisateur non autorisé.
- Erreur `Can't connect` / timeout : hôte ou port incorrect, ou connexions distantes bloquées par FreeDB.
- Erreur `Unknown database`: nom de base incorrect.
- Erreur `Table doesn't exist`: exécuter `schema.sql` dans la bonne base.
- Ouvrez `https://votre-app.onrender.com/health` pour tester la connexion.

## Schéma attendu

- `categorie_produits(id_categorie, libelle)`
- `produits(id_produit, designation, prix_vente, id_categorie)`
- `ventes(id_vente, date_vente, id_produit, quantite, prix_unitaire)`

Les champs et relations sont alignés sur le schéma fourni. Les suppressions sont protégées côté application lorsqu'un enregistrement est encore référencé.
