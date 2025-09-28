"""
Exercice de page de détails
"""

from flask import Flask, render_template, request, redirect
from datetime import datetime

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
    



@app.route('/service', methods=['GET', 'POST'])
def afficher_service():
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

# --------------------------------------------------------------------
# Fonction pour récupérer la liste des catégories de la bas de données
# --------------------------------------------------------------------

# def recuperer_categories():
#     """
#         Récupère toutes les catégories de la base de données
#             et les retourne sous forme de liste.
#     """

#     categories =[]

#     with bd.creer_connexion() as conn:
#         with conn.get_curseur() as curseur:
#             curseur.execute('SELECT nom_categorie FROM categories ORDER BY nom_categorie')
#             for ligne in curseur.fetchall():
#                 categories.append(ligne['nom_categorie'])
#     return categories


@app.route('/confirmation')
def confirmer():
    """Confirme l'ajout/modification du service"""

    message="Le service a été modifié avec succès!"
    
    return render_template ("confirmation.jinja", message=message)


@app.route('/ajout', methods=["GET", "POST"])
def ajout():
    """Page qui permet d'ajouter ou modifier un service"""

    categories =[]
    photo_service="images/gratisography.jpg"

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT nom_categorie FROM categories ORDER BY nom_categorie')
            for ligne in curseur.fetchall():
                categories.append(ligne['nom_categorie'])
    

    if  request.method == "POST":
        nom=request.form.get("nom", default="nom du service")
        localisation=request.form.get("localisation", default="localisation du service")
        description=request.form.get("description", default="Pas de description fournie")
        cout=request.form.get("cout", type=float, default=0.0)
        st=request.form.get("statut")
        statut = bool(st)
        categorie=request.form.get("categorie", default="")

        with bd.creer_connexion() as conn:
            with conn.get_curseur() as curseur:
                # Récupérer l'id_categorie correspondant au nom
                curseur.execute(
                "SELECT id_categorie FROM categories WHERE nom_categorie = %(nom)s",
                    {'nom': categorie}
                )
                id_categorie = curseur.fetchone()['id_categorie']
                #Ajout du nouveau service
                date_creation = datetime.now()
                curseur.execute(
                        """
                    INSERT INTO services
                    (id_categorie, titre, description, localisation, date_creation, actif, cout, photo)
                    VALUES
                    (%(id_categorie)s, %(titre)s, %(description)s, %(localisation)s,
                     %(date_creation)s, %(actif)s, %(cout)s, %(photo)s)
                    """,
                    {
                        'id_categorie': id_categorie,
                        'titre': nom,
                        'description': description,
                        'localisation': localisation,
                        'date_creation': date_creation,
                        'actif': statut,
                        'cout': cout,
                        'photo': photo_service,
                    }
                )
        return redirect("/confirmation", code=303)
    return render_template('ajout.jinja', categories=categories)



    # identifiant = request.args.get('id', type=int)
    # s = {}

    # TODO : faire try except et mettre dans logger

    # with bd.creer_connexion() as conn:
    #     with conn.get_curseur() as curseur:
    #         curseur.execute(
    #             'SELECT * FROM services where id_service=%(id)s',
    #             {
    #                 'id': identifiant
    #             }
    #         )
    #         s = curseur.fetchone()

    # return render_template('ajout.jinja', categories=categories, service=s)
    

if __name__ == "__main__":
    app.run(debug=True)