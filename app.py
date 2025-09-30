"""
Exercice de page de détails
"""

import re
import html
from datetime import datetime
from flask import Flask, render_template, request, redirect, abort, make_response
from jinja2 import select_autoescape
import bleach
from flask.logging import create_logger

import bd

regex_texte_court = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s]{1,50}$")
regex_description=re.compile(r"^.{5,2000}$")
regex_image=re.compile(r"^[A-Za-z0-9]{6,50}$")
regex_monetaire=re.compile(r'^\d{1,3}(,\d{3})*([.,]\d{1,2})?$')
regex_nombre = re.compile(r'^-?\d*\.?\d+$')

app = Flask(__name__)
logger = create_logger(app)


titres = {
        'fr_CA': "Bienvenue sur votre site d’échange de services entre particuliers!",
        'en_US': "Welcome to your community service exchange platform!",
        'en_CA': "Welcome to your Canadian service exchange platform!",
}


# def get_locale():
#     """Retourne la locale à utiliser"""

#     return request.cookies.get('langue', 'fr_CA')


#Caractères HTML
app.jinja_env.autoescape = select_autoescape(['html', 'xml', 'jinja'])

#Paramètres régionaux
app.config["BABEL_DEFAULT_LOCALE"] = "fr_CA"
locales = ["en_US", "en_CA", "fr_CA"]


services = []

@app.route('/')
def index():
    """Page d'index: Affiche les cinq derniers services de particuliers ajoutés selon la date d’ajout, 
    du plus récent au plus ancien."""
   
    # Récupérer les préférences stockées dans le cookie langue
    locale = request.cookies.get('langue', 'fr_CA')  
    if not locale:
        return redirect('/choisir_langue')

    titre = titres.get(locale, titres['fr_CA'])

    # TODO : faire try except et mettre dans logger

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            # curseur.execute('SELECT * FROM services WHERE actif = 1 ORDER BY date_creation DESC LIMIT 5')
            curseur.execute('SELECT s.* , c.nom_categorie AS categorie_nom FROM services s LEFT JOIN categories c ON s.id_categorie = c.id_categorie WHERE actif = 1 ORDER BY date_creation DESC LIMIT 5')
             
            services = curseur.fetchall()
            

    return render_template('index.jinja', titre=titre, titre_page= "Accueil",services=services)
    

@app.route('/choisir_langue', methods=['GET'])
def choisir_langue():

    langue = request.args.get("lang", default="fr_CA")
    reponse = make_response(redirect('/'))
    reponse.set_cookie('langue', langue)
    return reponse


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
    """Page qui permet d'ajouter un service"""

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
    classe_cout=""
    

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT nom_categorie FROM categories ORDER BY nom_categorie')
            for ligne in curseur.fetchall():
                categories.append(ligne['nom_categorie'])
    
    #Récupérer les valeurs des champs du formulaire
    if  request.method == 'POST':
        titre=bleach.clean(request.form.get("titre", default="")).strip()
        localisation=bleach.clean(request.form.get("localisation", default="")).strip()
        description=bleach.clean(request.form.get("description", default="")).strip()
        cout=request.form.get("cout", type=float, default=0.0)
        st=request.form.get("statut")
        statut = bool(st)
        categorie=request.form.get("categorie", default="")

        #validation du titre
        if not titre or not regex_texte_court.fullmatch(titre):
            erreur_titre = True
            classe_titre="is-invalid"
            # return abort(400)  
        else:
            classe_titre="is-valid"
        
        #validation de la localisation
        if not  localisation or not regex_texte_court.fullmatch(localisation):       
            erreur_localisation = True
            classe_localisation="is-invalid"
            # return abort(400)
        else: 
            classe_localisation="is-valid"

        #validation de la description
        if not description or not regex_description.fullmatch(description):
            erreur_description= True
            classe_description="is-invalid"
            # return abort(400)
        else:
            classe_description="is-valid"

        #Validation du coût

        if not regex_nombre.fullmatch(cout):
            erreur_cout= True
            classe_cout="is-invalid"
            # return abort(400)
        else:
            classe_cout="is-valid"

        #validation de la catégorie
        if not categorie :
            erreur_categorie = True
            classe_categorie="is-invalid"
            # return abort(400)
        else:
            classe_categorie="is-valid"
            
        if not erreur_titre and not erreur_localisation and not erreur_description and not erreur_cout and not erreur_categorie:

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
            # return redirect("/erreur_ajout", code=404)
     
            return render_template('ajout.jinja',titre_page="Ajout d'un service", 
                           categories=categories, 
                           classe_titre=classe_titre,
                           classe_localisation=classe_localisation,
                           classe_description=classe_description,
                           classe_categorie=classe_categorie,
                           classe_cout=classe_cout)
  
    return render_template('ajout.jinja',titre_page="Ajout d'un service", 
                           categories=categories, 
                           classe_titre=classe_titre,
                           classe_localisation=classe_localisation,
                           classe_description=classe_description,
                           classe_categorie=classe_categorie,
                           classe_cout=classe_cout)

@app.route('/modification', methods=["GET", "POST"])
def modifier():

    """Page qui permet de modifier un service"""

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
          
    categories =[]
    photo_service="images/gratisography.jpg"


    titre_service=service['titre']
    localisation_service=service['localisation']
    description_service=service['description']
    cout_service=service['cout']
    date_cr_service=service['date_creation']
    statut_service=service['actif']
 
    id_categorie_service=service['id_categorie']
    

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT nom_categorie FROM categories WHERE id_categorie =%(id_c)s',
                            {'id_c':id_categorie_service }
                            
                            )
            nom_categorie_service=curseur.fetchone()['nom_categorie']
            
            
    #         for ligne in curseur.fetchall():
    #             categories.append(ligne['nom_categorie'])
    
    #    "SELECT id_categorie FROM categories WHERE nom_categorie = %(nom)s",
    #                     {'nom': categorie}
    #                 )
    #                 id_categorie = curseur.fetchone()['id_categorie']
    erreur_titre = False
    erreur_localisation = False
    erreur_description = False
    erreur_categorie = False
    erreur_cout = False

    classe_titre= ""
    classe_localisation= ""
    classe_description= ""
    classe_cout= ""

    
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT nom_categorie FROM categories ORDER BY nom_categorie')
            for ligne in curseur.fetchall():
                categories.append(ligne['nom_categorie'])
                
    
    #Récupérer les valeurs des champs du formulaire
    if  request.method == 'POST':
        titre=bleach.clean(request.form.get("titre", default="")).strip()
        localisation=bleach.clean(request.form.get("localisation", default="")).strip()
        description=bleach.clean(request.form.get("description", default="")).strip()
        cout=request.form.get("cout", type=float, default=0.0)
        st=request.form.get("statut")
        statut = bool(st)
        # categorie=request.form.get("categorie", default="")


        # if not titre : 
        #     abort(400, "Paramètre 'titre' manquant")

        #validation du titre
        if not titre or not regex_texte_court.fullmatch(titre):
            erreur_titre = True
            classe_titre="is-invalid"
            return abort(400)
            
        else:
            classe_titre="is-valid"
        
        #validation de la localisation
        if not  localisation or not regex_texte_court.fullmatch(localisation):       
            erreur_localisation = True
            classe_localisation="is-invalid"
            return abort(400)
        else: 
            classe_localisation="is-valid"

              #Validation du coût

        if not regex_nombre.fullmatch(cout):
            erreur_cout= True
            classe_cout="is-invalid"
            return abort(400)
        else:
            classe_cout="is-valid"

        #validation de la description
        if not description or not regex_description.fullmatch(description):
            erreur_description= True
            classe_description="is-invalid"
            return abort(400)
        else:
            classe_description="is-valid"

            
        if not erreur_titre and not erreur_localisation and not erreur_description and not erreur_cout and not erreur_categorie:

            with bd.creer_connexion() as conn:
                with conn.get_curseur() as curseur:
                    # Récupérer l'id_categorie correspondant au nom
                    # curseur.execute(
                    # "SELECT id_categorie FROM categories WHERE nom_categorie = %(nom)s",
                    #     {'nom': categorie}
                    # )
                    # id_categorie = curseur.fetchone()['id_categorie']

                    curseur.execute(
                        """
                        UPDATE services 
                        SET titre = %(titre)s,
                            description = %(description)s,
                            localisation = %(localisation)s,
                            cout = %(cout)s,
                            actif = %(actif)s
                        WHERE id_service = %(id_service)s
                        """,
                        {
                            'titre': titre,
                            'description': description,
                            'localisation': localisation,
                            'cout': cout,
                            'actif': statut,
                            'id_service': identifiant 
                        }
)
                      
            return redirect("/confirmation", code=303)
        else:
            # return redirect("/erreur_ajout", code=404)
     
            return render_template('modification.jinja',titre_page="Modification d'un service", 
                           categories=categories, 
                           titre=titre_service,
                           localisation=localisation_service,
                           description=description_service,
                           cout=cout_service,
                           date_creation=date_cr_service,
                           statut=statut_service,
                           categorie_service=nom_categorie_service,

                           classe_titre=classe_titre,
                           classe_localisation=classe_localisation,
                           classe_description=classe_description,
                           classe_cout=classe_cout
                           )

  
    return render_template('modification.jinja',titre_page="Modification d'un service", 
                            categories=categories, 
                            titre=titre_service,
                            localisation=localisation_service,
                            description=description_service,
                            cout=cout_service,
                            date_creation=date_cr_service,
                            statut=statut_service,
                            categorie_service=nom_categorie_service,

                            classe_titre=classe_titre,
                            classe_localisation=classe_localisation,
                            classe_description=classe_description,
                            classe_cout=classe_cout
                           )

@app.route('/nos-services')
def lister_service():
    """Affiche la liste de tous les services proposés par les utilisateurs du site"""
    services= []
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
                            
            curseur.execute("SELECT titre FROM services")
            services = curseur.fetchall()
    
    return render_template('nos-services.jinja',titre_page="Nos services", services=services)


@app.errorhandler(400)
def parametre_manquant(erreur):
    """Pour les erreurs 400"""

    logger.exception(erreur)
    
    return render_template(
        'erreur.jinja',
        titre_page="Oups ! Une erreur est survenue",
        titre="Requête invalide",
        code=400,
        message="Un paramètre est manquant."
    ), 400


@app.errorhandler(404)
def inexistant(erreur):
    """Fonction qui gère l'erreur 404"""
    logger.exception(erreur)

    return render_template(
        "erreur.jinja",
        titre_page="Oups ! Une erreur est survenue",
        titre="Ressource introuvable", 
        code=404,
        message="Le service ou la page demandée n’existe pas ou n’est plus disponible.Veuillez vérifier l’adresse ou retourner à l’accueil."
        ), 404

@app.errorhandler(500)
def erreur_interne(erreur):
    """Fonction qui gère l'erreur 500"""

    logger.exception(erreur)
    return render_template(
        "erreur.jinja",
        titre_page="Oups ! Une erreur est survenue",
        titre="Problème technique",
        code=500,
        message="Nous rencontrons actuellement un problème technique lié à notre base de données. Veuillez réessayer plus tard. Si le problème persiste, contactez l’administrateur du site."
        ), 500




if __name__ == "__main__":
    app.run()