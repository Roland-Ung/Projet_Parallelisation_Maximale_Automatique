from maxpar import Task, TaskSystem  # Importe tes classes Task et TaskSystem depuis ton fichier maxpar.py
import time  # Importe le module time pour pouvoir utiliser sleep (pause) et mesurer le temps

# Variables globales qui servent de "mémoire partagée" entre les différentes tâches
X, Y, Z = 0, 0, 0

def runT1():
    global X  # On va modifier la variable X
    time.sleep(0.1) # Simulation d'un calcul (0.1 seconde)
    X = 10

def runT2():
    global Y  # On va modifier la variable Y
    time.sleep(0.1)  # Simulation d'un calcul (0.1 seconde)
    Y = 20

def runSomme():
    global X, Y, Z  # Accède aux variables X et Y pour lire, et Z pour écrire
    Z = X + Y

# Création des tâches
t1 = Task("T1", reads=[], writes=["X"], run=runT1) # T1 ne lit rien mais écrit dans X
t2 = Task("T2", reads=[], writes=["Y"], run=runT2) # T2 ne lit rien mais écrit dans Y
tSomme = Task("Somme", reads=["X", "Y"], writes=["Z"], run=runSomme) # Somme lit X et Y, écrit le résultat dans Z

# --- Configuration du système de tâches ---

# T2 attend T1, et Somme attend T1 et T2. Mais T1 et T2 vont être parallélisés après Bernstein
sys = TaskSystem([t1, t2, tSomme], {"T1": [], "T2": ["T1"], "Somme": ["T1", "T2"]})

# Vérification : on demande qui doit s'exécuter avant "Somme" selon le calcul de Bernstein
print("Dépendances de Somme :", sys.getDependencies("Somme"))
# Note : T1 et T2 seront toujours là car elles écrivent ce que Somme lit.

# --- Lancement des exécutions ---

print("Exécution séquentielle...")
sys.runSeq()  # Lance les tâches l'une après l'autre (Temps total estimé : 0.2s + calcul)
print(f"Résultat final de Z: {Z}")  # Affiche le résultat (devrait être 30)

print("Comparaison des performances :")
sys.parCost() # compare runSeq() et run() sur plusieurs répétitions

# On passe 'globals()' qui contient toutes les variables de ce fichier (X, Y, Z...)
sys.detTestRnd(globals())

# Visualisation
sys.draw()  # Ouvre une fenêtre pour montrer le graphe (T1 et T2 pointant vers Somme)
