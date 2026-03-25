from maxpar import Task, TaskSystem
import time  # Importe le module time pour pouvoir utiliser sleep (pause) et mesurer le temps

# Variables globales qui servent de "mémoire partagée" entre les différentes tâches
X, Y, Z = 0, 0, 0

def runT1():
    global X  # Indique que l'on va modifier la variable X définie à l'extérieur
    time.sleep(0.1) # Simulation d'un calcul qui prend du temps (0.1 seconde)
    X = 10  # Affecte la valeur 10 à X

def runT2():
    global Y  # Indique que l'on va modifier la variable Y définie à l'extérieur
    time.sleep(0.1)  # Simulation d'un calcul (0.1 seconde)
    Y = 20  # Affecte la valeur 20 à Y

def runSomme():
    global X, Y, Z  # Accède aux variables X et Y pour lire, et Z pour écrire
    Z = X + Y  # Calcule la somme et stocke le résultat dans Z

# Création des tâches
t1 = Task("T1", reads=[], writes=["X"], run=runT1) # T1 ne lit rien mais écrit dans X
t2 = Task("T2", reads=[], writes=["Y"], run=runT2) # T2 ne lit rien mais écrit dans Y
tSomme = Task("Somme", reads=["X", "Y"], writes=["Z"], run=runSomme) # Somme lit X et Y, écrit le résultat dans Z

# --- Configuration du système de tâches ---

initial_precedence = { # dictionnaire de précédence de départ (tout est enchainé)
    "T1": [], # T1 n'a pas de parent
    "T2": ["T1"], # T2 est l'enfant et attend son parent T1
    "Somme": ["T1", "T2"] # Somme attend T1 et T2
}

# On crée l'instance du système. C'est ici que Bernstein va "casser" la flèche entre T1 et T2
sys = TaskSystem([t1, t2, tSomme], initial_precedence)

# Vérification : on demande qui doit s'exécuter avant "Somme" selon le calcul de Bernstein
print("Dépendances de Somme :", sys.getDependencies("Somme"))
# Note : T1 et T2 seront toujours là car elles écrivent ce que Somme lit.

# --- Lancement des exécutions ---

print("Exécution séquentielle...")
sys.runSeq()  # Lance les tâches l'une après l'autre (Temps total estimé : 0.2s + calcul)
print(f"Résultat final de Z: {Z}")  # Affiche le résultat (devrait être 30)

print("Comparaison des performances :")
sys.parCost() # compare runSeq() et run() sur plusieurs répétitions

# Visualisation
sys.draw()  # Ouvre une fenêtre pour montrer le graphe (T1 et T2 pointent vers Somme)
