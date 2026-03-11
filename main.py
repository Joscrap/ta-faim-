#Les import
from flask import Flask, render_template, request, url_for, redirect, session

# on importe os, pour sécuriser le cookie de session
import os
#crypter les mots de passe dans la bdd
import bcrypt  

#on import mongo db
import pymongo 
#pour gére les ObjectId
from bson.objectid import ObjectId

#on import le .env pour sécuriser la connection a la base de donné
from dotenv import load_dotenv
load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

#connexion a la base de données
mongo = pymongo.MongoClient(mongo_uri)
#créer notre apli flask
app = Flask(__name__)

#Cookie de session utilisateur
app.secret_key = os.urandom(24)



#######################
### PAGE DU SITE ######
#######################



#accueil de connexion
@app.route('/')
def index():
    # Vérifier si l'utilisateur est connecté
    if 'util' in session:
        user = mongo.ta_faim.utilisateur.find_one({'nom': session['util']})
        
        # Si l'utilisateur existe
        if user:
            # S'il n'est pas encore dans un groupe, rediriger vers connexion_groupe
            if user.get('team') is None:
                return redirect(url_for('connexion_groupe'))
            # Sinon, il a un groupe → rediriger vers accueil
            return redirect(url_for('accueil'))

    # Personne n'est connecté → afficher la page publique
    return render_template('index.html')


###########################################################################################################################


# page d'accueil
@app.route('/accueil')
def accueil():
    #on vérifie si il est connecter
    if 'util' not in session:
        return redirect(url_for('login'))
    
    # on regarde dans la bdd si il y a un utilisateur qui a son nom avec le cookie de session
    user = mongo.ta_faim.utilisateur.find_one({'nom': session['util']})
    # on vérifie si il a une team
    if user.get('team') == None:
        # si non on l'envoie vers la page de connexion de groupe
        return redirect('/connexion_groupe')
    

    annonces = mongo.ta_faim.annonces.find({})
    return render_template('accueil.html', nom=session['util'], annonces=annonces)
    

###########################################################################################################################


# page pour afficher les annonce
@app.route('/annonce/<id_annonces>')
def annonce(id_annonces):
    # je récupère l'id unique de l'annonces
    db_annonces = mongo.ta_faim.annonces
    annonce = db_annonces.find_one({"_id": ObjectId(id_annonces)})
    return render_template("annonce_grand.html", annonce = annonce)


###########################################################################################################################


#logeout
@app.route('/logout')
def logout():
    session.clear()
    print("logout")
    return redirect(url_for('index'))


###########################################################################################################################


@app.route('/profil')
def profil():
    #on vérifie si il est connecter
    if 'util' not in session:
        return redirect(url_for('login'))
    
    # on regarde dans la bdd si il y a un utilisateur qui a son nom avec le cookie de session
    user = mongo.ta_faim.utilisateur.find_one({'nom': session['util']})
    # on vérifie si il a une team
    if user.get('team') == None:
        # si non on l'envoie vers la page de connexion de groupe
        return redirect('/connexion_groupe')
    
    nom = user.get('nom')
    groupe = user.get('team')

    return render_template("profil.html", nom=nom, groupe=groupe)


###########################################################################################################################


@app.route('/accueil_group')
def groupe():
    #on vérifie si il est connecter
    if 'util' not in session:
        return redirect(url_for('login'))
    
    # on regarde dans la bdd si il y a un utilisateur qui a son nom avec le cookie de session
    user = mongo.ta_faim.utilisateur.find_one({'nom': session['util']})
    # on vérifie si il a une team
    if user.get('team') == None:
        # si non on l'envoie vers la page de connexion de groupe
        return redirect('/connexion_groupe')
    
    return render_template("/accueil_group.html")


###########################################################################################################################


@app.route('/favori')
def favorie():
    #on vérifie si il est connecter
    if 'util' not in session:
        return redirect(url_for('login'))
    
    # on regarde dans la bdd si il y a un utilisateur qui a son nom avec le cookie de session
    user = mongo.ta_faim.utilisateur.find_one({'nom': session['util']})
    # on vérifie si il a une team
    if user.get('team') == None:
        # si non on l'envoie vers la page de connexion de groupe
        return redirect('/connexion_groupe')
    
    return render_template("favori.html")





#######################
### UTILISATEUR #######
#######################

# Route de login (Si l'on a déjà un compte)
@app.route('/login', methods=['POST', 'GET'])
def login():
    
    # Si on essaye de se connecter
    if request.method == 'POST':

        # On appelle la table utilisateur de la bdd
        db_utils = mongo.ta_faim.utilisateur
        util = db_utils.find_one({'nom': request.form['utilisateur']})

        # Si l'utilisateur existe
        if util:
            # On vérifie si le mot de passe est bon
            if bcrypt.checkpw(request.form['mot_de_passe'].encode('utf_8'),util['mdp']):
                session['util'] = request.form['utilisateur']
                user = mongo.ta_faim.utilisateur.find_one({
                'nom': session['util']
                })

                #on vérifie si a pas déjà un groupe pour l'envoyer directement sur la page d'accueil
                if user.get('team') == None:
                    return redirect(url_for("create_groupe"))
                else:
                    return redirect(url_for("accueil"))
                
            # Sinon on envoie un message d'erreur mot de passe incorrect
            else:
                return render_template('login.html', erreur="Le mot de passe est incorrect")
        # Sinon l'utilisateur n'existe pas
        else:
            return render_template('login.html', erreur="L'utilisateur n'existe pas")
    else:
        return render_template('login.html')


###########################################################################################################################


#page de registre
@app.route('/register', methods=['POST', 'GET'])
def register():

    #si on essaye de soummettre un formulaire
    if request.method == 'POST':
        #vérifier qu'un utilisateur du meme nom n'existe pas
        db_utili = mongo.ta_faim.utilisateur
        # si l'utilisateur existe déjà
        if (db_utili.find_one({'nom' : request.form['utilisateur']})):
            return render_template('register.html', erreur="Le nom d'utilisateur existe déjà")
        
        #sinon on crée l'utilisateur
        else:
            # on vérifie si le mot de passe est le même que la confiramtion
            if (request.form['mot_de_passe']) == (request.form['verif_mot_de_passe']):
                # on va cripter le mot de passse 
                mdp_encrypte = bcrypt.hashpw(request.form['mot_de_passe'].encode('utf-8'), bcrypt.gensalt())
                # j'ajoute l'utilisateur dans ma bdd
                db_utili.insert_one({
                    'nom' : request.form['utilisateur'],
                    'mdp' : mdp_encrypte,
                    'team' : None
                })
                #on le connecte avec un cookie de session
                session['util'] = request.form['utilisateur']
                #on retourne sur la page d'acceil
                return redirect(url_for('create_groupe'))

            else:
                return render_template('register.html', erreur="Les mots de passe ne sont pas identiques")

    else:
        return render_template('register.html')


###########################################################################################################################


#page connecxion groupe
@app.route('/connexion_groupe', methods=['POST', 'GET'])
def connexion_groupe():
    if 'util' not in session:
        return redirect(url_for('login'))
    
    # Si on essaye de se connecter
    elif request.method == 'POST':

        # On appelle la table utilisateur de la bdd
        db_team = mongo.ta_faim.team
        util = db_team.find_one({'nom': request.form['team']})

        # Si l'utilisateur existe
        if util:

            # On vérifie si le mot de passe est bon
            if bcrypt.checkpw(request.form['mot_de_passe'].encode('utf_8'),util['mdp']):
                db_utili = mongo.ta_faim.utilisateur
                db_utili.update_one(
                    {'nom': session['util']},
                    {'$set': {'team': request.form['team']}}
                )
                return redirect(url_for("accueil"))
            
            # Sinon on envoie un message d'erreur mot de passe incorrect
            else:
                return render_template('connexion_groupe.html', erreur="Le mot de passe est incorrect")
            
        # Sinon l'utilisateur n'existe pas
        else:
            return render_template('connexion_groupe.html', erreur="Le groupe n'existe pas")
    else:
        return render_template('connexion_groupe.html')


###########################################################################################################################


@app.route('/create_groupe', methods=['POST', 'GET'])
def create_groupe():

    if 'util' not in session:
        return redirect(url_for('login'))
    
    #si on essaye de soummettre un formulaire
    elif request.method == 'POST':
        #vérifier qu'une team du meme nom n'existe pas
        db_team = mongo.ta_faim.team
        db_utili = mongo.ta_faim.utilisateur
        # si la team existe déjà
        if (db_team.find_one({'nom' : request.form['team']})):
            return render_template('create_groupe.html', erreur="Le nom de la team existe déjà")
        
        #sinon on crée la team
        else:
            # on vérifie si le mot de passe est le même que la confiramtion
            if (request.form['mot_de_passe']) == (request.form['verif_mot_de_passe']):
                # on va cripter le mot de passse 
                mdp_encrypte = bcrypt.hashpw(request.form['mot_de_passe'].encode('utf-8'), bcrypt.gensalt())
                # j'ajoute la team dans ma bdd
                db_team.insert_one({
                    'nom' : request.form['team'],
                    'mdp' : mdp_encrypte
                })
                #on ajoute le nom de la team dans les info de l'utilisateur
                db_utili.update_one(
                    {'nom': session['util']},
                    {'$set': {'team': request.form['team']}
                })
                #on retourne sur la page d'acceil
                return redirect(url_for('accueil'))

            else:
                return render_template('create_groupe.html', erreur="Les mots de passe ne sont pas identiques")
    else:
        return render_template('create_groupe.html')


###########################################################################################################################


@app.route('/nouvelle_annonce', methods=['POST', 'GET'])
def nouvelle_annonce():
    if 'util' not in session:
        return redirect(url_for('login'))
    
    #si on essaye de soummettre un formulaire
    elif request.method == 'POST':
        if 'util' not in session:
            return render_template('nouvelle_annonce.html', erreur="Connectez-vous avant de publier une annonce")
        
        else:
            # j'ajoute l'annonce dans ma bdd
            mongo.ta_faim.annonces.insert_one({
                'titre' : request.form['titre'],
                'auteur' : session.get('util', 'Anonyme'),
                'description' : request.form['description'],
                'img' : "../static/img1.jpg"
            })
            #on retourne sur la page d'acceil
            return redirect(url_for('accueil'))
    else:
        return render_template('nouvelle_annonce.html')


###########################################################################################################################


@app.route('/quitter_team', methods=['POST'])
def quitter_team():
    
    db_utili = mongo.ta_faim.utilisateur

    db_utili.update_one(
        {'nom': session['util']},
        {'$set': {'team': None}}
    )

    return redirect(url_for('connexion_groupe'))

# execution
app.run(host='0.0.0.0', port=81)


###########################################################################################################################


@app.route('/coeur', methods=['POST'])
def coeur():
    db_utili = mongo.ta_faim.utilisateur

    db_utili.update_one(
        {'nom': session['util']},
        {'$set': {'favorie': None}}
    )
