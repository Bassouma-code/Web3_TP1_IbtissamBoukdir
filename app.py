"""
Exercice de page de détails
"""

import re
from flask import Flask, render_template, request, redirect
from datetime import datetime
import bd

regex_texte_court = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s]{1,50}$")
regex_description=re.compile(r"^.{5,2000}$")
regex_image=re.compile(r"^[A-Za-z0-9]{6,50}$")
regex_monetaire=re.compile(r'^\d{1,3}(,\d{3})*([.,]\d{1,2})?$')

app = Flask(__name__)



services = []

@app.route('/')
def index():
    """Page d'index: Affiche les cinq derniers services de particuliers ajoutés selon la date d’ajout, 
    du plus récent au plus ancien."""
   

    # TODO : faire try except et mettre dans logger

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            # curseur.execute('SELECT * FROM services WHERE actif = 1 ORDER BY date_creation DESC LIMIT 5')
            curseur.execute('SELECT s.* , c.nom_categorie AS categorie_nom FROM services s LEFT JOIN categories c ON s.id_categorie = c.id_categorie WHERE actif = 1 ORDER BY date_creation DESC LIMIT 5')
             
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
    
    return render_template ("confirmation.jinja",titre_page="Confirmation d'ajout de service", message=message)


@app.route('/ajout', methods=["GET", "POST"])
def ajout():
    """Page qui permet d'ajouter ou modifier un service"""

    categories =[]
    photo_service="images/gratisography.jpg"

    erreur_titre = False
    erreur_localisation = False
    erreur_description = False
    erreur_categorie = False
    erreur_cout = False


    classe_titre= ""
    classe_localisation= ""
    classe_description= ""
    classe_categorie= ""
    

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT nom_categorie FROM categories ORDER BY nom_categorie')
            for ligne in curseur.fetchall():
                categories.append(ligne['nom_categorie'])
    
    #Récupérer les valeurs des chamos du formulaire
    if  request.method == 'POST':
        titre=request.form.get("titre", default="")
        localisation=request.form.get("localisation", default="")
        description=request.form.get("description", default="")
        cout=request.form.get("cout", type=float, default=0.0)
        st=request.form.get("statut")
        statut = bool(st)
        categorie=request.form.get("categorie", default="")

        #validation du titre
        if not titre or not titre.strip() or not regex_texte_court.fullmatch(titre):
            erreur_titre = True
            classe_titre="is-invalid"
        else:
            classe_titre="is-valid"
        
        #validation de la localisation
        if not  localisation or not localisation.strip() or not regex_texte_court.fullmatch(localisation):       
            erreur_localisation = True
            classe_localisation="is-invalid"
        else: 
            classe_localisation="is-valid"

        #validation de la description
        if not description or not description.strip() or not regex_description.fullmatch(description):
            erreur_description= True
            classe_description="is-invalid"
        else:
            classe_description="is-valid"

        #validation de la catégorie
        if not categorie :
            erreur_categorie = True
            classe_categorie="is-invalid"
        else:
            classe_categorie="is-valid"
            

        if not erreur_titre and not erreur_localisation and not erreur_description and not erreur_categorie:

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
                            'titre': titre,
                            'description': description,
                            'localisation': localisation,
                            'date_creation': date_creation,
                            'actif': statut,
                            'cout': cout,
                            'photo': photo_service,
                        }
                    )
                      
            return redirect("/confirmation", code=303)
        else:
            return redirect("/erreur_ajout", code=404)
   
    return render_template('ajout.jinja',titre_page="Ajout/modification d'un service", 
                           categories=categories, 
                           classe_titre=classe_titre,
                           classe_localisation=classe_localisation,
                           classe_description=classe_description,
                           classe_categorie=classe_categorie)



@app.route('/erreur_ajout')
def erreur_ajout():

    """Affiche un message d'erreur si un détail de service inexistant"""
    message_erreur="Détails d’un service inexistant."

    #404
    return render_template('base.jinja', message_erreur=message_erreur)
  
@app.route('/nos-services')
def lister_service():
    """Affiche la liste de tous les services proposés par les utilisateurs du site"""
    services= []
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
                            
            curseur.execute("SELECT titre FROM services")
            services = curseur.fetchall()
    
    return render_template('nos-services.jinja',titre_page="Nos services", services=services)

if __name__ == "__main__":
    app.run(debug=True)