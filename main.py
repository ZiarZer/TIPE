# -*- coding: utf-8 -*-

#Kivy
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.picker import MDTimePicker, MDDatePicker
from kivymd.uix.dialog import MDDialog

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from kivy.core.window import Window
from kivy.clock import Clock

from kivy.garden.mapview import MapView
from kivy.garden.mapview import MapMarkerPopup

#Fichiers annexes .py
from scrollablelabel import ScrollableLabel
from checkpoints import CHECKPOINTS, distance_carre
from checkpoints import plus_proche_checkpoint, coordonnees_checkpoint

#Modules utiles
from math import sqrt
from hashlib import sha256
from datetime import datetime, timedelta
import sqlite3 as sql
import os
import re

SEMAINE = "Lundi Mardi Mercredi Jeudi Vendredi Samedi Dimanche".split()

bdd = sql.connect('tipe.db')
cursor = bdd.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS Chat
                (user_id INTEGER NOT NULL,
                    destinataire_id INTEGER NOT NULL,
                    time_msg datetime NOT NULL,
                    contenu TEXT NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS ConvRecentesChat
                (user_id INTEGER NOT NULL UNIQUE,
                    id_destinataires TEXT DEFAULT "",
                    PRIMARY KEY(user_id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Demandes
                (id INTEGER NOT NULL UNIQUE,
                    demandeur_id INTEGER NOT NULL,
                    aller_ou_retour boolean NOT NULL,
                    date_heure datetime NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    indications TEXT,
                    reservee_par INTEGER,
                    PRIMARY KEY(id AUTOINCREMENT))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Utilisateurs
                (id INTEGER NOT NULL UNIQUE,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    classe TEXT NOT NULL,
                    mail TEXT NOT NULL, 
                    mot_de_passe TEXT NOT NULL,
                    PRIMARY KEY(id AUTOINCREMENT))''')

bdd.commit()
bdd.close()


class PosterDemandePage(GridLayout):
    def __init__(self, aller_ou_retour, **kwargs):
        global user_info
        global SEMAINE
        
        super().__init__(**kwargs)
        
        self.aller_ou_retour = aller_ou_retour
        self.DATE = datetime.today()
        self.HEURE = datetime.strptime("07:00:00", '%H:%M:%S').time()

        DECALAGE = timedelta(days=1)

        ListeDatesPossibles = [self.DATE + DECALAGE * k for k in range(8)]
        #On peut faire une demande jusqu'à une semaine à l'avance

        self.cols = 2

        vals_spinner_date = tuple([SEMAINE[date.weekday()] + " " + date.strftime("%d/%m/%Y") for date in ListeDatesPossibles])

        if aller_ou_retour:
            #On a fixé le nombre de colonnes à 2 donc on coupe le texte en 2 pour le centrer
            self.add_widget(MDLabel(text="Nouvelle demande de covoit", halign="right"))
            self.add_widget(MDLabel(text="urage pour aller au lycée", halign="left"))
        else:
            self.add_widget(MDLabel(text="Nouvelle demande de covoit", halign="right"))
            self.add_widget(MDLabel(text="urage pour partir du lycée", halign="left"))

        self.add_widget(MDLabel(text="Jour où vous voulez être déposé :"))

        self.date_spinner = Spinner(text = vals_spinner_date[0], values = vals_spinner_date)
        self.add_widget(self.date_spinner)


        if aller_ou_retour:
            self.add_widget(MDLabel(text="Heure à laquelle vous voulez arriver au lycée :"))
        else:
            self.add_widget(MDLabel(text="Heure à laquelle vous voulez partir du lycée :"))

        self.bouton_reglage_heure = Button(text="07:00")
        self.bouton_reglage_heure.bind(on_press = self.show_time_picker)
        self.add_widget(self.bouton_reglage_heure)

        if aller_ou_retour:
            self.add_widget(MDLabel(text="Lieu de rendez-vous :"))
        else:
            self.add_widget(MDLabel(text="Destination :"))

        self.localisation = Spinner(text="Anse-Bertrand", values=tuple([checkp[0] for checkp in CHECKPOINTS]))
        self.add_widget(self.localisation)

        self.add_widget(MDLabel(text="Indications optionnelles concernant le trajet"))

        self.indications = TextInput(text="", multiline=False)
        self.add_widget(self.indications)

        self.bouton_menu_demandes = Button(text = "Retour au menu des demandes")
        self.bouton_menu_demandes.bind(on_press = self.retour_menu_demandes)
        self.add_widget(self.bouton_menu_demandes)

        self.bouton_demande = Button(text = "Publier ma demande")
        self.bouton_demande.bind(on_press = self.post_demande)
        self.add_widget(self.bouton_demande)

    def show_time_picker(self, _):
        time_pick = MDTimePicker()
        time_pick.set_time(self.HEURE)
        time_pick.bind(time=self.get_time)
        time_pick.open()

    def get_time(self, instance, time):
        self.HEURE = time
        self.bouton_reglage_heure.text = time.strftime("%H:%M")

    def retour_menu_demandes(self, _):
        objet_app.screen_manager.current = "Menu Demandes"

    def post_demande(self, _):
        global user_info
        aller_ou_retour = self.aller_ou_retour
        localisation = coordonnees_checkpoint(self.localisation.text)

        heure = self.HEURE
        date_mauvais_format = (self.date_spinner.text.split()[1]).split("/")
        date_bon_format = "/".join([date_mauvais_format[0], date_mauvais_format[1], date_mauvais_format[2][2:]])

        date = datetime.strptime(date_bon_format, '%d/%m/%y')
        annee, mois, jour = date.year, date.month, date.day
        date_heure = datetime(annee, mois, jour, heure.hour, heure.minute, 0)

        indications = self.indications.text
        if indications=="":
            indications="Aucune"

        jour_demande = datetime.now().strftime("%Y-%m-%d")
        bdd = sql.connect("tipe.db")
        cursor = bdd.cursor()
        cursor.execute('''SELECT COUNT() FROM Demandes
            WHERE date_heure LIKE ? AND aller_ou_retour=?''', (jour_demande+"%", int(aller_ou_retour)))
        nb_demandes = cursor.fetchone()

        if type(nb_demandes) == tuple and nb_demandes[0] > 1:
            text_erreur = "Pas plus d'une demande aller et une demande retour par jour"
            MDDialog(title="Demande non postée", text=text_erreur).open()
            bdd.close()

        elif date_heure < datetime.now():
            text_erreur = "Vous ne pouvez pas poster une demande pour un moment passé"
            MDDialog(title="Demande non postée", text=text_erreur).open()
            bdd.close()            

        else:
            if type(user_info) == tuple:
                infos = (user_info[0], aller_ou_retour, date_heure, localisation[0], localisation[1], indications)
                cursor.execute('''INSERT INTO Demandes
                    (demandeur_id, aller_ou_retour, date_heure, latitude, longitude, indications)
                    VALUES (?, ?, ?, ?, ?, ?)''', infos)
                bdd.commit()
                bdd.close()

            if aller_ou_retour:
                objet_app.screen_manager.current = "Infos Demande Aller"
            else:
                objet_app.screen_manager.current = "Infos Demande Partir"

class InfosDemandePage(GridLayout):
    def __init__(self, aller_ou_retour, **kwargs):
        super().__init__(**kwargs)
        global SEMAINE
        global user_info
        self.cols = 1

        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute("SELECT * FROM Demandes WHERE demandeur_id=? ORDER BY date_heure DESC", (user_info[0],))
        last_demande = cursor.fetchone()
        bdd.close()

        if type(last_demande) == tuple:
            aller_ou_retour, date_heure, lat, lon, indications = last_demande[2:7]

            date_heure = datetime.strptime(date_heure, "%Y-%m-%d %H:%M:%S")
            date_heure = SEMAINE[date_heure.weekday()]+" "+date_heure.strftime("%d/%m/%Y %H:%M:%S")

            resume_demande = ("Lieu de rendez-vous : ", "Destination : ")[aller_ou_retour]
            resume_demande += plus_proche_checkpoint(lat, lon)[0]+  "\n"#Pour donner un nom au lieu de rendez-vous
            resume_demande += "Date et heure d'arrivée au lycée : " + date_heure + "\n"
            resume_demande += "Indications : " + indications
            self.add_widget(MDLabel(text=resume_demande, halign="center", valign="middle"))

        self.btn_retour_menu_d = Button(text="Retour au menu des demandes")
        self.btn_retour_menu_d.bind(on_press = self.retour_menu_d)
        self.add_widget(self.btn_retour_menu_d)

    def retour_menu_d(self, _):
        objet_app.screen_manager.current = "Menu Demandes"

class ConnexionPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols=2

        if os.path.isfile("prev_connexion.txt"):
            with open("prev_connexion.txt","r") as f:
                d = f.read().split(",")
                prev_mail, prev_password = d[0], d[1]
        else:
            prev_mail, prev_password = "",""


        self.add_widget(MDLabel(text="Adresse mail :"))

        self.mail = TextInput(text=prev_mail,multiline=False)
        self.add_widget(self.mail)

        self.add_widget(MDLabel(text="Mot de passe :"))

        self.password = TextInput(text=prev_password, multiline=False, password=True)
        self.add_widget(self.password)

        self.bouton_pas_de_compte = Button(text="Vous n'avez pas de compte ? Inscrivez-vous")
        self.bouton_pas_de_compte.bind(on_press = self.pas_de_compte)
        self.add_widget(self.bouton_pas_de_compte)

        self.bouton_connexion = Button(text="Se connecter")
        self.bouton_connexion.bind(on_press = self.infos_connexion)
        self.add_widget(self.bouton_connexion)

    def infos_connexion(self, instance):
        mail = self.mail.text
        password = self.password.text

        with open("prev_connexion.txt","w") as f:
            f.write(f"{mail},{password}")

        Clock.schedule_once(self.connect,0.1)

    def connect(self, _):
        global user_info
        mail = self.mail.text
        password = self.password.text
        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute("SELECT * FROM Utilisateurs WHERE mail=?",(mail,))

        user = cursor.fetchone()

        bdd.close()

        if type(user)==tuple and sha256(password.encode()).hexdigest() == user[5]:
            user_info = user
            objet_app.run_space()
            objet_app.screen_manager.current = "My Space"

        else:
            objet_app.screen_manager.current = "Connexion"
            text_erreur = "L'adresse mail et le mot de passe entrés ne sont pas corrects."
            dialog = MDDialog(title="Échec de la connexion",text = text_erreur)
            dialog.open()

    def pas_de_compte(self, _):
        objet_app.screen_manager.current = "Inscription"

class InscriptionPage(GridLayout):
    classes_dispo = ("MP","PC","PSI","MPSI","PCSI","BCPST1","BCPST2","2nde","1ere","Terminale")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols=2

        self.champ_nom = MDLabel(text="Nom :")
        self.add_widget(self.champ_nom)
        self.nom = TextInput(multiline=False)
        self.add_widget(self.nom)

        self.add_widget(MDLabel(text="Prénom :"))
        
        self.prenom = TextInput(multiline=False)
        self.add_widget(self.prenom)

        self.add_widget(MDLabel(text="Classe :"))
        self.classe = Spinner(text="MP", values=self.classes_dispo)
        self.add_widget(self.classe)

        self.champ_mail = MDLabel(text="Adresse Mail :")
        self.add_widget(self.champ_mail)
        self.mail = TextInput(multiline=False)
        self.add_widget(self.mail)

        self.champ_mdp = MDLabel(text="Mot de passe :")
        self.add_widget(self.champ_mdp)
        self.mot_de_passe = TextInput(multiline=False, password=True)
        self.add_widget(self.mot_de_passe)

        self.champ_confirme_mdp = MDLabel(text="Confirmer le mot de passe :")
        self.add_widget(self.champ_confirme_mdp)
        self.confirme_mdp = TextInput(multiline=False, password=True)
        self.add_widget(self.confirme_mdp)

        self.bouton_deja_compte = Button(text="J'ai déjà un compte, je veux me connecter")
        self.bouton_deja_compte.bind(on_press = self.deja_compte)
        self.add_widget(self.bouton_deja_compte)

        self.bouton_inscription = Button(text="S'inscrire")
        self.bouton_inscription.bind(on_press = self.infos_inscription)
        self.add_widget(self.bouton_inscription)

    def infos_inscription(self, instance):
        nom = (self.nom.text).upper()
        prenom = self.prenom.text
        classe = self.classe.text
        mail = (self.mail.text).lower()
        mot_de_passe = self.mot_de_passe.text
        confirme_mdp = self.confirme_mdp.text

        regex_mail = "^[a-z0-9.-]+@[a-z0-9.-]+\.[a-z]{2,}"

        longueur_mdp_ok = len(mot_de_passe)>5
        confirmation_mdp_ok = (mot_de_passe==confirme_mdp)
        mail_ok = (mail==re.match(regex_mail, mail).group())
        tous_champs_remplis = all([nom, prenom, classe, mail, mot_de_passe, confirme_mdp])

        Champs_ok = [tous_champs_remplis, mail_ok, longueur_mdp_ok, confirmation_mdp_ok]


        if all(Champs_ok):
            infos = (nom, prenom, classe, mail, sha256(mot_de_passe.encode()).hexdigest())
            self.add_database(infos)
            objet_app.run_space()
            objet_app.screen_manager.current = "Confirmation Inscription"
        else:
            Erreurs_possibles = ["Tous les champs sont obligatoires.",
            "L'adresse mail entrée n'est pas valide.",
            "Le mot de passe est trop court : il doit être d'au moins 6 caractères.",
            "La confirmation du mot de passe doit être identique au mot de passe."
            ]
            Erreurs_commises = []
            for k in range(4):
                if not Champs_ok[k]:
                    Erreurs_commises.append(Erreurs_possibles[k])


            dialogue_erreur = MDDialog(title="Échec de l'inscription", text="\n".join(Erreurs_commises))
            dialogue_erreur.open()

    def add_database(self, infos):
        global user_info
        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute('''INSERT INTO Utilisateurs (nom, prenom, classe, mail, mot_de_passe)
            VALUES(?,?,?,?,?)''', infos)
        bdd.commit()

        cursor.execute("SELECT * FROM Utilisateurs WHERE mail=?", (infos[3],))
        user_info = cursor.fetchone()

        cursor.execute("INSERT INTO ConvRecentesChat (user_id) VALUES(?)", (user_info[0],))
        bdd.commit()
        bdd.close()

    def deja_compte(self, instance):
        objet_app.screen_manager.current = "Connexion"

class ConfirmationInscriptionPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols=1
        self.rows=2
        self.add_widget(MDLabel(text="Votre compte a été enregistré avec succès !", halign='center'))

        self.bouton_my_space = Button(text="Accéder à mon espace")
        self.bouton_my_space.bind(on_press=self.go_to_my_space)
        self.add_widget(self.bouton_my_space)

    def go_to_my_space(self, _):
        objet_app.screen_manager.current = "My Space"

class MySpacePage(GridLayout):
    def __init__(self, **kwargs):
        global user_info
        super().__init__(**kwargs)

        self.cols = 2

        nom_prenom = MDLabel(text = user_info[1] + " " + user_info[2],
                            halign = "center",
                            valign = "middle")
        self.add_widget(nom_prenom)

        self.bouton_conversations = Button(text="Conversations")
        self.bouton_conversations.bind(on_press = self.voir_conversations)
        self.add_widget(self.bouton_conversations)

        self.bouton_menu_demande = Button(text="Menu des demandes")
        self.bouton_menu_demande.bind(on_press = self.menu_demande)
        self.add_widget(self.bouton_menu_demande)

        self.btn_close = Button(text="Quitter l'application")
        self.btn_close.bind(on_press = self.fermer_app)
        self.add_widget(self.btn_close)

    def voir_conversations(self, _):
        objet_app.screen_manager.current = "Choix Conversation"

    def menu_demande(self, _):
        objet_app.screen_manager.current = "Menu Demandes"

    def fermer_app(self, instance):
        objet_app.stop()

class MenuDemandesPage(GridLayout):
    def __init__(self, **kwargs):
        global user_info
        super().__init__(**kwargs)

        self.cols = 1

        txt_btn = "Voir les émissions de gaz à effet de serre évitées grâce à l'application"
        self.btn_voir_reductions = Button(text = txt_btn)
        self.btn_voir_reductions.bind(on_press = self.voir_reductions)
        self.add_widget(self.btn_voir_reductions)
        
        box_haut = BoxLayout(orientation = 'horizontal')
        box_bas = BoxLayout(orientation = 'horizontal')

        self.btn_aller = Button(text="Mes demandes pour aller au lycée")
        self.btn_aller.bind(on_press = self.aller)
        box_haut.add_widget(self.btn_aller)

        self.btn_partir = Button(text="Mes demandes pour partir du lycée")
        self.btn_partir.bind(on_press = self.partir)
        box_haut.add_widget(self.btn_partir)

        self.btn_carte_demandes = Button(text="Carte des demandes")
        self.btn_carte_demandes.bind(on_press = self.carte_demandes)
        box_bas.add_widget(self.btn_carte_demandes)

        self.btn_retour_espace = Button(text="Retour à mon espace")
        self.btn_retour_espace.bind(on_press = self.retour_espace)
        box_bas.add_widget(self.btn_retour_espace)

        self.add_widget(box_haut)
        self.add_widget(box_bas)

    def aller(self, _):
        objet_app.screen_manager.current = "Poster Demande Aller"

    def partir(self, _):
        objet_app.screen_manager.current = "Poster Demande Partir"

    def carte_demandes(self, _):
        objet_app.screen_manager.current = "Carte Demandes"

    def retour_espace(self, _):
        objet_app.screen_manager.current = "My Space"

    def voir_reductions(self, _):
        objet_app.screen_manager.current = "Réductions"

class ChoixConvPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        global user_info

        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        if type(user_info)==tuple:
            cursor.execute("SELECT id_destinataires FROM ConvRecentesChat WHERE user_id = ?", (user_info[0],))
        data = cursor.fetchone()
        bdd.close()

        if type(data)==tuple and data != (",",) and data[0] != None:
            liste_destinataires = data[0].split(",")

            while "" in liste_destinataires:
                liste_destinataires.remove("")

            L_id_destinataires = [int(dest_id) for dest_id in liste_destinataires]
            L_spinner = []

            bdd = sql.connect('tipe.db')
            cursor=bdd.cursor()
            for id_ in L_id_destinataires:
                cursor.execute("SELECT * FROM Utilisateurs WHERE id=?", (id_,))

                desti_info = cursor.fetchone()
                nom_prenom = desti_info[1]+" "+desti_info[2]
                L_spinner.append(nom_prenom)
            bdd.close()

            box_chat = BoxLayout(orientation='horizontal')

            self.spinner_destinataire = Spinner(values=tuple(L_spinner))
            if len(L_spinner)>0:
                self.spinner_destinataire.text = L_spinner[0]

            box_chat.add_widget(self.spinner_destinataire)

            self.btn_go_chat = Button(text="Aller à cette discussion")
            self.btn_go_chat.bind(on_press = self.vers_chat_page)
            box_chat.add_widget(self.btn_go_chat)
            self.add_widget(box_chat)

        else:
            self.add_widget(MDLabel(text="Vous n'avez pas encore de conversation.",halign="center"))

        self.bouton_retour_espace = Button(text="<| Retour")
        self.bouton_retour_espace.bind(on_press = self.retour_espace)
        self.add_widget(self.bouton_retour_espace)

    def vers_chat_page(self, _):
        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        nom, prenom = (self.spinner_destinataire.text).split(" ")

        cursor.execute("SELECT * FROM Utilisateurs WHERE nom=? AND prenom=?", (nom, prenom))

        destinataire = cursor.fetchone()
        bdd.close()

        try:
            objet_app.screen_manager.remove_widget(screen_chat_widget)
        except:
            pass
        screen_chat_widget = Screen(name="Page Chat")
        screen_chat_widget.add_widget(ChatPage(destinataire = destinataire))
        objet_app.screen_manager.add_widget(screen_chat_widget)
        objet_app.screen_manager.current = "Page Chat"

    def retour_espace(self, *_):
        objet_app.screen_manager.current = "My Space"

class ReductionsPage(GridLayout):
    lat_baimbridge, lon_baimbridge = 16.2691916, -61.5053831

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        global user_info
        self.cols = 1

        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute('''SELECT latitude, longitude FROM Demandes
            WHERE date_heure<DATE('now') AND reservee_par IS NOT NULL''')
        lat_lon_demandes = cursor.fetchall()

        somme_km_economises = 0
        for coordonnees in lat_lon_demandes:
            lat, lon = coordonnees[0], coordonnees[1]
            somme_km_economises += self.distance_au_lycee(lat = lat, lon = lon)

        reduction_emissions = round(0.19 * somme_km_economises, 2)

        msg_reduction = f"L'application a permis d'éviter {reduction_emissions} kg de gaz à effet de serre !"
        self.add_widget(MDLabel(text = msg_reduction, halign='center'))

        self.btn_retour = Button(text = "Retour au menu des demandes")
        self.btn_retour.bind(on_press = self.retour_menu_demandes)
        self.add_widget(self.btn_retour)

    def distance_au_lycee(self, lat, lon):
        dlat_en_km = 173.517 * (lat - self.lat_baimbridge)
        dlon_en_km = 105.804 * (lon - self.lon_baimbridge)
        return sqrt(dlat_en_km**2 + dlon_en_km**2)

    def retour_menu_demandes(self, **kwargs):
        objet_app.screen_manager.current = "Menu Demandes"


class ChatPage(GridLayout):
    def __init__(self, destinataire, **kwargs):
        super().__init__(**kwargs)
        global user_info
        self.destinataire = destinataire
        self.cols = 1
        self.rows = 3

        box_haut = BoxLayout(orientation='horizontal')

        box_haut.bouton_retour_espace = Button(text="<| Retour", size_hint=[0.33, 1])
        box_haut.bouton_retour_espace.bind(on_press = self.retour_espace)
        box_haut.add_widget(box_haut.bouton_retour_espace)

        nom_prenom = destinataire[1]+" "+destinataire[2]
        box_haut.add_widget(MDLabel(text=nom_prenom, halign="center", size_hint=[0.67,1]))

        self.add_widget(box_haut)

        self.historique = ScrollableLabel(height = Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.historique)

        self.new_message = TextInput(width = Window.size[0]*0.8, size_hint_x=None)

        self.send = Button(text="Envoyer")
        self.send.bind(on_press=self.envoi_message)

        bottom_line = GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)

        self.charger_historique(destinataire = destinataire)

        Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_once(self.focus_text_input, 1)

    def charger_historique(self, destinataire):
        global user_info
        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute('''SELECT * FROM Chat
            WHERE (user_id=? AND destinataire_id=?) OR (user_id=? AND destinataire_id=?)
            ORDER BY time_msg''', (user_info[0],destinataire[0],destinataire[0],user_info[0]))
        MSG = cursor.fetchall()
        bdd.close()

        for msg in MSG:
            if msg[0]==user_info[0]:
                msg_a_ajouter = f"[color=dd2020]Vous[/color] > {msg[3]}"
            else:
                f"[color=20dd20]{destinataire[1]} {destinataire[2]}[/color] > {msg[3]}"

            self.historique.update_chat(msg_a_ajouter)

    def retour_espace(self, *_):
        objet_app.screen_manager.current = "My Space"

    def focus_text_input(self, _):
        self.new_message.focus = True

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode==40 and self.new_message.text not in ("", "\n", " "):
            self.envoi_message(None)

    def envoi_message(self, _ = None):
        global user_info

        destinataire = self.destinataire
        message = self.new_message.text

        if message[0]=="\n":
            message=message[1:]
        self.new_message.text = ""

        if message:
            bdd = sql.connect('tipe.db')
            cursor = bdd.cursor()

            if type(user_info)==tuple:

                cursor.execute('''SELECT id_destinataires FROM ConvRecentesChat
                    WHERE user_id=?''',(user_info[0],))
                try:
                    dests_user = cursor.fetchone()[0].split(",")
                except:
                    dests_user = []

                cursor.execute('''SELECT id_destinataires FROM ConvRecentesChat
                    WHERE user_id=?''',(destinataire[0],))
                try:
                    dests_autre = cursor.fetchone()[0].split(",")
                except:
                    dests_autre = []

                if str(destinataire[0]) in dests_user:
                    dests_user.remove(str(destinataire[0]))

                if str(user_info[0]) in dests_autre:
                    dests_autre.remove(str(user_info[0]))

                dests_user = ",".join([str(destinataire[0])] + dests_user)
                dests_autre = ",".join([str(user_info[0])] + dests_autre)

                cursor.execute('''UPDATE ConvRecentesChat SET id_destinataires=?
                    WHERE user_id=?''', (dests_user,user_info[0]))
                bdd.commit()

                cursor.execute('''UPDATE ConvRecentesChat SET id_destinataires=?
                    WHERE user_id=?''', (dests_autre,destinataire[0]))
                bdd.commit()

                infos_msg = (user_info[0], destinataire[0], datetime.now(), message)
                cursor.execute('''INSERT INTO Chat
                    (user_id, destinataire_id, time_msg, contenu)
                    VALUES(?,?,?,?)''', infos_msg)
                bdd.commit()
            bdd.close()

        Clock.schedule_once(self.focus_text_input, 0.1)

        self.historique.update_chat(f"[color=dd2020]Vous[/color] > {message}")

class UserMarker(MapMarkerPopup):
    demande_data = []

    def on_release(self):
        PopupInfos(self.demande_data).open()

class CarteDemandesPage(MapView):
    global user_info
    get_users_timer = None
    liste_id_demandes=[]

    def lancer_chrono(self):
        #Après 1 seconde sans que l'utilisateur ait bougé la carte
        #(pour éviter de charger sans cesse des demandes),
        #on cherche les demandes qui pourront être visibles sur l'écran
        try:
            self.get_users_timer.cancel()
        except:
            pass
        self.get_users_timer = Clock.schedule_once(self.obtenir_demandes_visibles, 1)

    def obtenir_demandes_visibles(self, *args):
        global user_info
        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()

        min_lat, min_lon, max_lat, max_lon = self.get_bbox()
        vars_sql = (min_lat, max_lat, min_lon, max_lon, user_info[0])
        cursor.execute('''SELECT * FROM Demandes
            WHERE latitude>=? AND latitude<=? AND
            longitude>=? AND longitude<=?
            AND demandeur_id <> ? AND reservee_par IS NULL''', vars_sql)

        demandes_non_reservees = cursor.fetchall()

        for demande in demandes_non_reservees:
            id_demande = demande[0]
            self.add_demande(demande, 'r')

        if type(user_info)==tuple:
            vars_sql = (min_lat, max_lat, min_lon, max_lon, user_info[0])
            cursor.execute('''SELECT * FROM Demandes
                WHERE latitude>=? AND latitude<=? AND
                longitude>=? AND longitude<=?
                AND reservee_par=?''', vars_sql)

            for demande in cursor.fetchall():
                id_demande = demande[0]
                self.add_demande(demande, 'b')

    def add_demande(self, demande, couleur):
        lat, lon = demande[4], demande[5]
        marker = UserMarker(lat=lat, lon=lon, source='marker_'+couleur+'.png')
        marker.demande_data = demande

        self.add_marker(marker)

        id_demande = demande[0]
        if id_demande not in self.liste_id_demandes:
            self.liste_id_demandes.append(id_demande)

    def retour_menu_demandes(self, **kwargs):
        objet_app.screen_manager.current = "Menu Demandes"

class PopupInfos(Popup):
    def __init__(self, demande_data):
        super().__init__()
        self.demande_data = demande_data

        bdd = sql.connect('tipe.db')
        cursor = bdd.cursor()
        cursor.execute("SELECT nom, prenom FROM Utilisateurs WHERE id=?", (demande_data[1],))
        user = " ".join(cursor.fetchone())

        aller_ou_retour = ("Part du lycée", "Va au lycée")[demande_data[2]]
        date_heure,latitude, longitude, indications, reservee_par=demande_data[3:8]

        date_heure = datetime.strptime(date_heure, "%Y-%m-%d %H:%M:%S")
        j_semaine = "Lundi Mardi Mercredi Jeudi Vendredi Samedi Dimanche".split()[date_heure.isoweekday()]
        date_heure = "Date et heure : "+j_semaine +" "+date_heure.strftime("%d/%m/%Y à %-H:%M")
        indications = "Indications : "+indications

        lieu = "Aux environs de : " + plus_proche_checkpoint(latitude, longitude)[0]

        infos_demande = "\n".join([aller_ou_retour, date_heure, lieu, indications])

        self.box_content = BoxLayout(orientation="vertical")
        self.box_content.add_widget(Label(text=infos_demande))

        self.box_boutons = BoxLayout(orientation="horizontal")

        self.btn_chat = Button(text="Chatter avec cette personne")
        self.btn_chat.bind(on_release=self.go_to_chat)
        self.box_content.add_widget(self.btn_chat)

        if reservee_par==None:
            self.btn_reserver = Button(text="Prendre cette demande en charge")
            self.btn_reserver.bind(on_release=self.reserver)
            self.box_content.add_widget(self.btn_reserver)

        self.box_content.add_widget(self.box_boutons)


        self.title = user
        self.content = self.box_content
        self.size_hint=[0.7, 0.7]
        self.open()

    def reserver(self, _):
        bdd=sql.connect("tipe.db")
        cursor = bdd.cursor()

        vars_sql = (user_info[0], self.demande_data[0])

        cursor.execute("UPDATE Demandes SET reservee_par=? WHERE id=?", vars_sql)
        bdd.commit()
        bdd.close()

        self.dismiss()
        objet_app.screen_manager.current = "My Space"

    def go_to_chat(self, _):
        demandeur_id = self.demande_data[1]

        bdd = sql.connect("tipe.db")
        cursor = bdd.cursor()
        cursor.execute("SELECT * FROM Utilisateurs WHERE id=?", (demandeur_id,))
        demandeur = cursor.fetchone()
        bdd.close()

        self.dismiss()

        try:
            objet_app.screen_manager.remove_widget(screen_chat_widget)
        except:
            pass
        screen_chat_widget = Screen(name="Page Chat")
        screen_chat_widget.add_widget(ChatPage(destinataire = demandeur))
        objet_app.screen_manager.add_widget(screen_chat_widget)
        objet_app.screen_manager.current = "Page Chat"

class CovoiturageApp(MDApp):
    def build(self):
        self.screen_manager = ScreenManager()

        screen = Screen(name="Connexion")
        screen.add_widget(ConnexionPage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Inscription")
        screen.add_widget(InscriptionPage())
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def run_space(self):
        screen = Screen(name="Poster Demande Aller")
        screen.add_widget(PosterDemandePage(aller_ou_retour=True))
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Poster Demande Partir")
        screen.add_widget(PosterDemandePage(aller_ou_retour=False))
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Infos Demande Aller")
        screen.add_widget(InfosDemandePage(aller_ou_retour=True))
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Infos Demande Partir")
        screen.add_widget(InfosDemandePage(aller_ou_retour=False))
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Menu Demandes")
        screen.add_widget(MenuDemandesPage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Choix Conversation")
        screen.add_widget(ChoixConvPage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="My Space")
        screen.add_widget(MySpacePage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Confirmation Inscription")
        screen.add_widget(ConfirmationInscriptionPage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Carte Demandes")
        screen.add_widget(CarteDemandesPage())
        self.screen_manager.add_widget(screen)

        screen = Screen(name="Réductions")
        screen.add_widget(ReductionsPage())
        self.screen_manager.add_widget(screen)

        return self.screen_manager

user_info = None

objet_app = CovoiturageApp()
objet_app.run()
