#  Projet SMARTBIN - Notre Poubelle Intelligente

Bienvenue sur le projet de notre groupe ! Nous avons conçu un prototype de poubelle connectée capable de reconnaître la couleur des déchets (rouge ou bleu) pour les trier automatiquement dans le bon bac sans intervention humaine.


## Comment ça marche concrètement ?

Notre projet fonctionne grâce à trois fichiers qui discutent ensemble en continu :

1. **`cam.py` (L'analyse d'image en Python)** : Ce script récupère les images de la caméra en temps réel. S'il voit un déchet rouge ou bleu, il ajoute +1 au compteur sur l'écran (et sauvegarde le score dans un petit fichier texte pour ne pas perdre le compte si tout s'éteint). Ensuite, il envoie un signal ('R' ou 'B') à l'Arduino.
2. **`arduino_tri.ino` (Les moteurs et capteurs)** : Dès que l'Arduino reçoit le signal du PC, il s'active ! Il fait tourner un tapis roulant et oriente un petit bras articulé (servomoteur) pour pousser le déchet dans le bon bac. En plus, si vous approchez votre main, son capteur ultrason ouvre automatiquement le couvercle de la poubelle.
3.  **`esp32_cam.ino` (La caméra sans fil)** : C'est le code de notre caméra. Elle se connecte au Wi-Fi de la pièce et diffuse le flux vidéo en local sur une adresse IP (comme une petite caméra de sécurité).


##  Le matériel qu'on a utilisé
* 1 carte **Arduino** (le cerveau mécanique)
* 1 caméra **ESP32-CAM** (les yeux du système)
* 1 capteur de distance à ultrason **HC-SR04** (pour l'approche des mains)
* 2 **Servomoteurs** (un pour ouvrir le couvercle, un pour orienter le tri)
* 1 module **Relais** (pour allumer/éteindre le moteur du tapis roulant)


##  Comment lancer le projet sur votre PC

### 1. Préparer les cartes
* Téléverser le code sur votre caméra ESP32 et notez son adresse IP.
* Brancher l'Arduino à l'ordinateur avec son câble USB et téléverser son code de contrôle.

### 2. Lancer le programme Python
Ouvrez votre terminal et installez les outils nécessaires avec cette commande :
```bash
pip install opencv-python numpy pyserial requests
```
Mettez la bonne adresse IP de la caméra dans le fichier `cam.py`, puis lancez-le :
```bash
python cam.py
```
Une fenêtre s'ouvre avec le flux vidéo en direct, les statistiques de tri et un bouton "RESET" cliquable à la souris pour remettre les compteurs à zéro !
