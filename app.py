import os
from decimal import Decimal, InvalidOperation
from datetime import date
from urllib.parse import quote_plus

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

db = SQLAlchemy()


def build_database_uri():
    # Option 1: define DATABASE_URL directly in Render.
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Support common mysql:// URLs by explicitly selecting PyMySQL.
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        return database_url

    # Option 2: provide the FreeDB connection details separately.
    host = os.getenv("MYSQL_HOST")
    name = os.getenv("MYSQL_DATABASE")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    port = os.getenv("MYSQL_PORT", "3306")

    if not all([host, name, user, password]):
        raise RuntimeError(
            "Configuration MySQL manquante. Définissez DATABASE_URL ou "
            "MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER et MYSQL_PASSWORD."
        )

    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}?charset=utf8mb4"
    )


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "connect_args": {"connect_timeout": 10},
}
db.init_app(app)


class CategorieProduit(db.Model):
    __tablename__ = "categorie_produits"

    id_categorie = db.Column(db.Integer, primary_key=True, autoincrement=True)
    libelle = db.Column(db.String(100), nullable=False, unique=True)
    produits = db.relationship("Produit", back_populates="categorie")


class Produit(db.Model):
    __tablename__ = "produits"

    id_produit = db.Column(db.Integer, primary_key=True, autoincrement=True)
    designation = db.Column(db.String(150), nullable=False)
    prix_vente = db.Column(db.Numeric(10, 2), nullable=False)
    id_categorie = db.Column(
        db.Integer,
        db.ForeignKey("categorie_produits.id_categorie"),
        nullable=False,
    )
    categorie = db.relationship("CategorieProduit", back_populates="produits")
    ventes = db.relationship("Vente", back_populates="produit")


class Vente(db.Model):
    __tablename__ = "ventes"

    id_vente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_vente = db.Column(db.Date, nullable=False)
    id_produit = db.Column(
        db.Integer,
        db.ForeignKey("produits.id_produit"),
        nullable=False,
    )
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    produit = db.relationship("Produit", back_populates="ventes")


@app.get("/")
def accueil():
    return render_template(
        "index.html",
        nb_categories=CategorieProduit.query.count(),
        nb_produits=Produit.query.count(),
        nb_ventes=Vente.query.count(),
        dernieres_ventes=Vente.query.order_by(Vente.date_vente.desc(), Vente.id_vente.desc()).limit(5).all(),
    )


# -------------------- CATEGORIES --------------------

@app.get("/categories")
def categories():
    elements = CategorieProduit.query.order_by(CategorieProduit.libelle).all()
    return render_template("categories.html", categories=elements)


@app.route("/categories/ajouter", methods=["GET", "POST"])
def ajouter_categorie():
    if request.method == "POST":
        libelle = request.form.get("libelle", "").strip()
        if not libelle:
            flash("Le libellé est obligatoire.", "danger")
        else:
            db.session.add(CategorieProduit(libelle=libelle))
            try:
                db.session.commit()
                flash("Catégorie ajoutée avec succès.", "success")
                return redirect(url_for("categories"))
            except IntegrityError:
                db.session.rollback()
                flash("Cette catégorie existe déjà ou les données sont invalides.", "danger")
    return render_template("categorie_form.html", titre="Ajouter une catégorie", categorie=None)


@app.route("/categories/<int:id>/modifier", methods=["GET", "POST"])
def modifier_categorie(id):
    categorie = db.get_or_404(CategorieProduit, id)
    if request.method == "POST":
        libelle = request.form.get("libelle", "").strip()
        if not libelle:
            flash("Le libellé est obligatoire.", "danger")
        else:
            categorie.libelle = libelle
            try:
                db.session.commit()
                flash("Catégorie modifiée.", "success")
                return redirect(url_for("categories"))
            except IntegrityError:
                db.session.rollback()
                flash("Ce libellé est déjà utilisé.", "danger")
    return render_template("categorie_form.html", titre="Modifier une catégorie", categorie=categorie)


@app.post("/categories/<int:id>/supprimer")
def supprimer_categorie(id):
    categorie = db.get_or_404(CategorieProduit, id)
    if categorie.produits:
        flash("Impossible de supprimer cette catégorie : elle contient des produits.", "warning")
    else:
        db.session.delete(categorie)
        db.session.commit()
        flash("Catégorie supprimée.", "success")
    return redirect(url_for("categories"))


# -------------------- produitsS --------------------

@app.get("/produits")
def produits():
    elements = Produit.query.join(CategorieProduit).order_by(Produit.designation).all()
    return render_template("produits.html", produits=elements)


def lire_prix(champ):
    try:
        valeur = Decimal(request.form.get(champ, "").replace(",", "."))
        if valeur < 0:
            raise InvalidOperation
        return valeur
    except (InvalidOperation, ValueError):
        return None


@app.route("/produits/ajouter", methods=["GET", "POST"])
def ajouter_produit():
    categories_disponibles = CategorieProduit.query.order_by(CategorieProduit.libelle).all()
    if request.method == "POST":
        designation = request.form.get("designation", "").strip()
        prix = lire_prix("prix_vente")
        id_categorie = request.form.get("id_categorie", type=int)
        categorie = db.session.get(CategorieProduit, id_categorie) if id_categorie else None

        if not designation or prix is None or categorie is None:
            flash("Vérifiez la désignation, le prix et la catégorie.", "danger")
        else:
            db.session.add(Produit(designation=designation, prix_vente=prix, id_categorie=id_categorie))
            db.session.commit()
            flash("Produit ajouté.", "success")
            return redirect(url_for("produits"))
    return render_template("produit_form.html", titre="Ajouter un produit", produit=None, categories=categories_disponibles)


@app.route("/produits/<int:id>/modifier", methods=["GET", "POST"])
def modifier_produit(id):
    produit = db.get_or_404(Produit, id)
    categories_disponibles = CategorieProduit.query.order_by(CategorieProduit.libelle).all()
    if request.method == "POST":
        designation = request.form.get("designation", "").strip()
        prix = lire_prix("prix_vente")
        id_categorie = request.form.get("id_categorie", type=int)
        categorie = db.session.get(CategorieProduit, id_categorie) if id_categorie else None
        if not designation or prix is None or categorie is None:
            flash("Vérifiez la désignation, le prix et la catégorie.", "danger")
        else:
            produit.designation = designation
            produit.prix_vente = prix
            produit.id_categorie = id_categorie
            db.session.commit()
            flash("Produit modifié.", "success")
            return redirect(url_for("produits"))
    return render_template("produit_form.html", titre="Modifier un produit", produit=produit, categories=categories_disponibles)


@app.post("/produits/<int:id>/supprimer")
def supprimer_produit(id):
    produit = db.get_or_404(Produit, id)
    if produit.ventes:
        flash("Impossible de supprimer ce produit : il est déjà présent dans des ventes.", "warning")
    else:
        db.session.delete(produit)
        db.session.commit()
        flash("Produit supprimé.", "success")
    return redirect(url_for("produits"))


# -------------------- ventesS --------------------

@app.get("/ventes")
def ventes():
    elements = Vente.query.join(Produit).order_by(Vente.date_vente.desc(), Vente.id_vente.desc()).all()
    return render_template("ventes.html", ventes=elements)


@app.route("/ventes/ajouter", methods=["GET", "POST"])
def ajouter_vente():
    produits_disponibles = Produit.query.order_by(Produit.designation).all()
    if request.method == "POST":
        date_texte = request.form.get("date_vente", "")
        id_produit = request.form.get("id_produit", type=int)
        quantite = request.form.get("quantite", type=int)
        prix = lire_prix("prix_unitaire")
        produit = db.session.get(Produit, id_produit) if id_produit else None
        try:
            date_vente = date.fromisoformat(date_texte)
        except ValueError:
            date_vente = None

        if not produit or not date_vente or not quantite or quantite <= 0 or prix is None:
            flash("Vérifiez la date, le produit, la quantité et le prix unitaire.", "danger")
        else:
            db.session.add(Vente(
                date_vente=date_vente,
                id_produit=id_produit,
                quantite=quantite,
                prix_unitaire=prix,
            ))
            db.session.commit()
            flash("Vente enregistrée.", "success")
            return redirect(url_for("ventes"))
    return render_template("vente_form.html", produits=produits_disponibles, aujourd_hui=date.today().isoformat())


@app.post("/ventes/<int:id>/supprimer")
def supprimer_vente(id):
    vente = db.get_or_404(Vente, id)
    db.session.delete(vente)
    db.session.commit()
    flash("Vente supprimée.", "success")
    return redirect(url_for("ventes"))


@app.get("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200
    except Exception:
        app.logger.exception("Échec de la connexion MySQL")
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
