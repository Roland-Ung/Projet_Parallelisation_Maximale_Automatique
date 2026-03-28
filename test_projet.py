from maxpar import Task, TaskSystem  # Importe les classes du fichier maxpar.py
import time  # Importe le module time pour pouvoir utiliser sleep (pause) et mesurer le temps

X, Y, Z = 0, 0, 0

def runT1():
    global X  # On va modifier la variable X
    time.sleep(0.1) # Simulation d'un calcul (0.1 seconde)
    X = 1

def runT2():
    global Y  # On va modifier la variable Y
    time.sleep(0.1)  # Simulation d'un calcul (0.1 seconde)
    Y = 2

def runTsomme():
    global X, Y, Z  # Accède aux variables X et Y pour lire, et Z pour écrire
    Z = X + Y

# Création des tâches
t1 = Task("T1", reads=[], writes=["X"], run=runT1) # T1 ne lit rien mais écrit dans X
t2 = Task("T2", reads=[], writes=["Y"], run=runT2) # T2 ne lit rien mais écrit dans Y
tSomme = Task("Somme", reads=["X", "Y"], writes=["Z"], run=runTsomme) # Somme lit X et Y, écrit le résultat dans Z

# T2 attend T1, et Somme attend T1 et T2. Mais T1 et T2 vont être parallélisés après Bernstein
sys = TaskSystem([t1, t2, tSomme], {"T1": [], "T2": ["T1"], "Somme": ["T1", "T2"]})

t1.run()
t2.run()
tSomme.run()
print(f"X: {X}, Y: {Y}, Z: {Z}")

print("Dépendances de Somme :", sys.getDependencies("Somme")) # Qui doit s'éxécuter avant Somme
print("Comparaison des performances :")
sys.parCost() # compare runSeq() et run() sur plusieurs répétitions
sys.detTestRnd(globals()) # globals() contient toutes les variables globales du fichier (X, Y, Z)
sys.draw()  # Ouvre une fenêtre pour montrer le graphe (T1 et T2 pointant vers Somme)
