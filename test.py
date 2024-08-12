from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Configuration de l'application Flask
app = Flask(__name__)

# Définir le chemin de la base de données
database_path = os.path.join('C:', os.sep, 'Users', 'chaki_oyvbka2', 'OneDrive' ,'Documents', 'KCAL', 'instance', 'foods.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser SQLAlchemy
db = SQLAlchemy(app)

# Définir un modèle de test
class TestModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

# Fonction pour tester la connexion à la base de données
def test_db_connection():
    with app.app_context():
        try:
            # Créer toutes les tables (y compris TestModel)
            db.create_all()
            
            # Ajouter une entrée de test
            test_entry = TestModel(name='Test Entry')
            db.session.add(test_entry)
            db.session.commit()
            
            # Vérifier si l'entrée a été ajoutée avec succès
            entry = TestModel.query.first()
            if entry:
                print("Connexion réussie !")
                print(f"Entrée de test : {entry.name}")
            else:
                print("La connexion a réussi, mais aucune entrée de test n'a été trouvée.")
        
        except Exception as e:
            print("Erreur lors de la connexion à la base de données :", str(e))

if __name__ == '__main__':
    test_db_connection()
