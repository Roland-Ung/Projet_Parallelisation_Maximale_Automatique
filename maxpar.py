import threading  # Pour lancer plusieurs fonctions en même temps (parallélisme)
import time       # Pour mesurer le temps et faire des pauses
import networkx as nx  # Pour créer la structure du graphe (les bulles et les flèches)
import matplotlib.pyplot as plt  # Pour afficher le dessin du graphe à l'écran

class Task:
    # Le "formulaire" pour créer une tâche
    def __init__(self, name="", reads=None, writes=None, run=None):
        self.name = name  # Le nom de la tâche (ex: "T1")
        # Si l'utilisateur n'a rien mis dans reads, on crée une liste vide
        if reads == None:
            self.reads = []
        else:
            self.reads = reads
            
        # Si l'utilisateur n'a rien mis dans writes, on crée une liste vide
        if writes == None:
            self.writes = []
        else:
            self.writes = writes
            
        self.run = run  # La fonction (le code) que la tâche doit exécuter

class TaskSystem:
    # Le constructeur qui prépare tout le système
    def __init__(self, tasks, precedence_dict):
        # On crée un dictionnaire vide pour ranger nos objets tâches
        self.tasks = {}
        for t in tasks: # Pour chaque tâche reçue dans la liste
            self.tasks[t.name] = t # On la range avec son nom (ex: self.tasks["T1"])
            
        self.precedence = precedence_dict # On garde les règles de départ
        self._validate_inputs() # On vérifie s'il n'y a pas d'erreurs de noms
        
        # On calcule le graphe final (celui qui est optimisé)
        self.max_parallel_graph = self._compute_max_parallelism()

    def _validate_inputs(self):
        # On vérifie que chaque nom dans les règles existe bien dans la liste des tâches
        for nom_tache in self.precedence:
            if nom_tache not in self.tasks:
                print("ERREUR : La tâche " + nom_tache + " n'existe pas.")
            
            # On vérifie aussi les parents (dépendances)
            liste_parents = self.precedence[nom_tache]
            for p in liste_parents:
                if p not in self.tasks:
                    print("ERREUR : Le parent " + p + " n'existe pas.")

    def _bernstein(self, t1_name, t2_name):
        # On récupère les deux objets tâches pour comparer leurs variables
        t1 = self.tasks[t1_name]
        t2 = self.tasks[t2_name]
        
        # On transforme les listes de variables en "Ensembles" (sets) pour comparer
        R1 = set(t1.reads)  # Lecture de T1
        W1 = set(t1.writes) # Écriture de T1
        R2 = set(t2.reads)  # Lecture de T2
        W2 = set(t2.writes) # Écriture de T2
        
        # On vérifie les 3 cas de conflit (Bernstein)
        # .isdisjoint() veut dire "n'ont rien en commun"
        conflit1 = not W1.isdisjoint(R2) # T1 écrit ce que T2 lit
        conflit2 = not W2.isdisjoint(R1) # T2 écrit ce que T1 lit
        conflit3 = not W1.isdisjoint(W2) # Les deux écrivent au même endroit
        
        # Si un des conflits existe, on renvoie True (elles ne sont pas parallélisables)
        if conflit1 or conflit2 or conflit3:
            return True
        else:
            return False

    def _compute_max_parallelism(self):
        # On crée un nouveau dictionnaire pour le graphe optimisé
        nouveau_graphe = {}
        for nom in self.tasks:
            nouveau_graphe[nom] = [] # Liste vide de successeurs pour chaque tâche
            
        # On regarde les règles de départ
        for enfant in self.precedence:
            parents = self.precedence[enfant]
            for p in parents:
                # On ne garde la flèche que si Bernstein dit que c'est risqué
                if self._bernstein(p, enfant):
                    nouveau_graphe[p].append(enfant) # On ajoute la flèche p -> enfant
                    
        return nouveau_graphe

    def getDependencies(self, nomTache):
        # On veut savoir qui doit finir AVANT nomTache dans le graphe optimisé
        liste_predecesseurs = []
        # On parcourt notre graphe (parent -> liste d'enfants)
        for parent in self.max_parallel_graph:
            enfants = self.max_parallel_graph[parent]
            # Si notre tâche est dans la liste des enfants de ce parent
            if nomTache in enfants:
                liste_predecesseurs.append(parent) # On ajoute le parent à la liste
        return liste_predecesseurs

    def runSeq(self):
        # On transforme notre dictionnaire en un vrai objet Graphe NetworkX
        G = nx.DiGraph(self.max_parallel_graph)
        # On demande à NetworkX l'ordre logique (T1 avant Somme, etc.)
        ordre = list(nx.topological_sort(G))
        
        for nom in ordre:
            self.tasks[nom].run() # On lance la fonction de la tâche

    def run(self):
        # Exécution parallèle par étapes
        G = nx.DiGraph(self.max_parallel_graph)
        deja_fait = [] # Tâches terminées
        a_faire = list(self.tasks.keys()) # Tâches restantes
        
        while len(a_faire) > 0:
            pret_a_lancer = [] # Tâches qui n'ont plus de parents à attendre
            
            for t in a_faire:
                # On récupère les parents de la tâche dans le graphe
                parents = list(G.predecessors(t))
                tous_finis = True
                for p in parents:
                    if p not in deja_fait:
                        tous_finis = False
                
                if tous_finis == True:
                    pret_a_lancer.append(t) # La tâche est prête !
            
            ouvriers = [] # Liste des threads (fils d'exécution)
            for nom in pret_a_lancer:
                tache_objet = self.tasks[nom]
                # On prépare un ouvrier pour lancer la fonction
                nouveau_thread = threading.Thread(target=tache_objet.run)
                ouvriers.append(nouveau_thread)
                nouveau_thread.start() # L'ouvrier commence son travail
                
            for o in ouvriers: # On attend que tous les ouvriers du groupe finissent
                o.join()
                
            for nom in pret_a_lancer: # Mise à jour des listes
                deja_fait.append(nom)
                a_faire.remove(nom)

    def draw(self):
        # Dessine le graphe à l'écran
        G = nx.DiGraph(self.max_parallel_graph)
        nx.draw(G, with_labels=True, node_color='lightgreen', node_size=1500)
        plt.show()

    def parCost(self):
        # Mesure du temps séquentiel
        start_seq = time.time()
        self.runSeq()
        temps_seq = time.time() - start_seq
        
        # Mesure du temps parallèle
        start_par = time.time()
        self.run()
        temps_par = time.time() - start_par
        
        print("Résultat Temps Séquentiel : " + str(round(temps_seq, 4)) + " s")
        print("Résultat Temps Parallèle : " + str(round(temps_par, 4)) + " s")
