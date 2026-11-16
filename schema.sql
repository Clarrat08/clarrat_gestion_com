-- À exécuter dans la base MySQL déjà créée chez FreeDB.
-- Ne pas exécuter CREATE DATABASE si FreeDB ne vous accorde pas ce droit.

CREATE TABLE IF NOT EXISTS categorie_produits (
    id_categorie INT AUTO_INCREMENT PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS produits (
    id_produit INT AUTO_INCREMENT PRIMARY KEY,
    designation VARCHAR(150) NOT NULL,
    prix_vente DECIMAL(10,2) NOT NULL,
    id_categorie INT NOT NULL,
    CONSTRAINT fk_produit_categorie
        FOREIGN KEY (id_categorie)
        REFERENCES categorie_produits(id_categorie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ventes (
    id_vente INT AUTO_INCREMENT PRIMARY KEY,
    date_vente DATE NOT NULL,
    id_produit INT NOT NULL,
    quantite INT NOT NULL,
    prix_unitaire DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_vente_produit
        FOREIGN KEY (id_produit)
        REFERENCES produits(id_produit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
