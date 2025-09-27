"""
Exercice de page de détails
"""

from flask import Flask, render_template, request

import bd

app = Flask(__name__)

services = []

@app.route('/')
def index():
    """Page d'index: Affiche les cinq derniers services de particuliers ajoutés selon la date d’ajout, 
    du plus récent au plus ancien."""
   

    # TODO : faire try except et mettre dans logger

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT * FROM services WHERE actif = 1 ORDER BY date_creation DESC LIMIT 5')
            services = curseur.fetchall()
    return render_template('index.jinja', titre_page= "Accueil",services=services)
    


@app.route('/ajout')
def ajout():
    """Page qui permet d'ajouter ou modifier un service"""
    identifiant = request.args.get('id', type=int)
    s = {}

    # TODO : faire try except et mettre dans logger

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                'SELECT * FROM services where id_service=%(id)s',
                {
                    'id': identifiant
                }
            )
            s = curseur.fetchone()

    return render_template('ajout.jinja', service=s)


@app.route('/service', methods=['GET', 'POST'])
def service():
    """Page qui permet d'afficher toutes les informations d'un service"""
    identifiant = request.args.get('id', type=int)
    service = {}

    # TODO : faire try except et mettre dans logger

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                '''
            SELECT s.*, c.nom_categorie AS categorie_nom
            FROM services s
            LEFT JOIN categories c ON s.id_categorie = c.id_categorie
            WHERE s.id_service = %(id_service)s
            ''',
            {'id_service': identifiant}
            )
            service = curseur.fetchone()

    return render_template('service.jinja', titre_page="Détails d'un service", service=service)



app.run()