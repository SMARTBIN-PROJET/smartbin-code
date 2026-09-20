# smartbin-code
Code de traitement d'image (OpenCV) optimisé pour le tri automatique de la SmartBin. Analyse le flux de l'ESP32-CAM via requêtes HTTP, filtre les couleurs (masques HSV rouge/bleu), gère un compteur persistant (JSON) et envoie des commandes instantanées à l'Arduino (COM9) avec un délai anti-rebond calibré à 4,5s.
