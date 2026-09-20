import cv2
import numpy as np
import serial
import time
import requests
import json
import os

# ==============================================================================
# CONFIGURATION
# ==============================================================================
ESP32_URL = "http://172.20.10.2/capture"  
PORT_SERIE_ARDUINO = 'COM9' 
BAUD_RATE = 9600

SEUIL_PIXELS_MIN = 2000 

# OPTIMISATION : Réduit à 4.5s pour correspondre pile au cycle mécanique de votre poubelle
DELAI_ANTI_REBOND = 4.5 
dernier_envoi_temps = 0

# --- AJOUT MODULE DE COMPTAGE (Variables globales) ---
compteur_rouge = 0
compteur_bleu = 0
total_dechets = 0

# --- CONFIGURATION FICHIER DE SAUVEGARDE ---
FICHIER_SAUVEGARDE = "compteur_dechets.json"

def charger_sauvegarde():
    global compteur_rouge, compteur_bleu, total_dechets
    if os.path.exists(FICHIER_SAUVEGARDE):
        try:
            with open(FICHIER_SAUVEGARDE, 'r') as f:
                donnees = json.load(f)
                compteur_rouge = donnees.get("rouge", 0)
                compteur_bleu = donnees.get("bleu", 0)
                total_dechets = donnees.get("total", 0)
                print(f"-> Sauvegarde chargee : Rouge={compteur_rouge}, Bleu={compteur_bleu}, Total={total_dechets}")
        except Exception as e:
            print(f"-> Erreur lors du chargement de la sauvegarde : {e}")

def enregistrer_sauvegarde():
    try:
        donnees = {
            "rouge": compteur_rouge,
            "bleu": compteur_bleu,
            "total": total_dechets
        }
        with open(FICHIER_SAUVEGARDE, 'w') as f:
            json.dump(donnees, f, indent=4)
    except Exception as e:
        print(f"-> Erreur lors de l'enregistrement : {e}")

# --- ENREGISTREMENT DE L'ACTION DU BOUTON RESET (CLIC SOURIS) ---
def gerer_clic_bouton(event, x, y, flags, param):
    global compteur_rouge, compteur_bleu, total_dechets
    if event == cv2.EVENT_LBUTTONDOWN:
        if 310 <= x <= 410 and 5 <= y <= 45:
            compteur_rouge = 0
            compteur_bleu = 0
            total_dechets = 0
            enregistrer_sauvegarde()
            print("-> Tous les compteurs ont ete remis a 0.")

# Chargement automatique des données historiques
charger_sauvegarde()

# ==============================================================================
# INITIALISATION DE L'ARDUINO
# ==============================================================================
print("Connexion à l'Arduino sur le port " + PORT_SERIE_ARDUINO + "...")
try:
    arduino = serial.Serial(PORT_SERIE_ARDUINO, BAUD_RATE, timeout=1)
    arduino.setDTR(True)
    arduino.setRTS(True)
    time.sleep(3) 
    arduino.reset_input_buffer()
    arduino.reset_output_buffer()
    print("-> Connecté à l'Arduino avec succès.")
except Exception as e:
    print(f"-> Erreur de connexion série : {e}")
    arduino = None

print("\nDémarrage du flux d'analyse d'image...")

# --- PARAMÈTRES RÉSEAU DE PERFORMANCE (ANTI-LATENCE) ---
ENTETES_PERFORMANCE = {
    'Connection': 'close',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

NOM_FENETRE = "Flux Tri Automatique ESP32-CAM"
cv2.namedWindow(NOM_FENETRE)
cv2.setMouseCallback(NOM_FENETRE, gerer_clic_bouton)

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================
while True:
    try:
        reponse = requests.get(ESP32_URL, timeout=0.8, headers=ENTETES_PERFORMANCE)
        if reponse.status_code != 200:
            continue
        tableau_octets = np.frombuffer(reponse.content, dtype=np.uint8)
        frame = cv2.imdecode(tableau_octets, cv2.IMREAD_COLOR)
        if frame is None:
            continue
    except Exception as e:
        time.sleep(0.01)
        continue

    temps_actuel = time.time()
    flou = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(flou, cv2.COLOR_BGR2HSV)

    # Masques HSV (Rouge et Bleu)
    rouge_bas1, rouge_haut1 = np.array([0, 120, 70]), np.array([10, 255, 255])
    rouge_bas2, rouge_haut2 = np.array([170, 120, 70]), np.array([180, 255, 255])
    masque_rouge = cv2.add(cv2.inRange(hsv, rouge_bas1, rouge_haut1), cv2.inRange(hsv, rouge_bas2, rouge_haut2))
    
    bleu_bas, bleu_haut = np.array([90, 120, 70]), np.array([130, 255, 255])
    masque_bleu = cv2.inRange(hsv, bleu_bas, bleu_haut)

    nb_pixels_rouge = cv2.countNonZero(masque_rouge)
    nb_pixels_bleu = cv2.countNonZero(masque_bleu)

    # Logique de détection et incrémentation des compteurs
    if temps_actuel - dernier_envoi_temps > DELAI_ANTI_REBOND:
        if nb_pixels_rouge > SEUIL_PIXELS_MIN and nb_pixels_rouge > nb_pixels_bleu:
            print("[RECONNAISSANCE] Déchet Rouge détecté.")
            compteur_rouge += 1
            total_dechets += 1
            enregistrer_sauvegarde() 
            if arduino:
                arduino.reset_output_buffer() # Force la libération du canal de communication
                arduino.write(b'R')
            dernier_envoi_temps = temps_actuel

        elif nb_pixels_bleu > SEUIL_PIXELS_MIN and nb_pixels_bleu > nb_pixels_rouge:
            print("[RECONNAISSANCE] Déchet Bleu détecté.")
            compteur_bleu += 1
            total_dechets += 1
            enregistrer_sauvegarde() 
            if arduino:
                arduino.reset_output_buffer() # Force la libération du canal de communication
                arduino.write(b'B')
            dernier_envoi_temps = temps_actuel

    # ==========================================================================
    # --- MODULE D'AFFICHAGE GRAPHIQUE ---
    # ==========================================================================
    cv2.rectangle(frame, (5, 5), (290, 110), (0, 0, 0), -1)
    
    cv2.putText(frame, f"Statistiques de Tri", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"- Dechets Rouges : {compteur_rouge}", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.putText(frame, f"- Dechets Bleus  : {compteur_bleu}", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    cv2.putText(frame, f"TOTAL COLLECTE    : {total_dechets}", (15, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Bouton RESET
    cv2.rectangle(frame, (310, 5), (410, 45), (0, 140, 255), -1)
    cv2.putText(frame, "RESET", (328, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    if nb_pixels_rouge > SEUIL_PIXELS_MIN:
        cv2.putText(frame, "DETECTION : ROUGE", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    elif nb_pixels_bleu > SEUIL_PIXELS_MIN:
        cv2.putText(frame, "DETECTION : BLEU", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.imshow(NOM_FENETRE, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if arduino:
    arduino.close()
cv2.destroyAllWindows()
print("Programme arrêté.")
