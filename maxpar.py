import threading  # Pour lancer plusieurs fonctions en même temps (parallélisme)
import time       # Pour mesurer le temps et faire des pauses
import random
import networkx as nx  # Pour créer la structure du graphe (les bulles et les flèches)
import matplotlib.pyplot as plt  # Pour afficher le dessin du graphe à l'écran

class Task:
    # Les caractéristiques pour créer une tâche
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
            
        self.run = run  # La fonction que la tâche doit exécuter

class TaskSystem:
    # Construction d'un système de tâches
    def __init__(self, tasks, precedence_dict):        
        self.tasks = {} # On crée un dictionnaire vide pour ranger les tâches
        for t in tasks:
            if t.name in self.tasks: # On vérifie s'il y a des doublons (2.4)
                raise ValueError(f"ERREUR : Le nom de tâche '{t.name}' est dupliqué !")
            self.tasks[t.name] = t # Pour chaque tâche on la range avec son nom (ex: self.tasks["T1"])
            
        self.precedence = precedence_dict # On garde les règles de départ
        self._validate_inputs() # On vérifie s'il n'y a pas d'erreurs de noms
        self.max_parallel_graph = self._compute_max_parallelism() # le graphe final (celui optimisé)
    
    # 2.4 Validation des entrées (noms existants)
    def _validate_inputs(self):
        # On vérifie que chaque nom dans les règles existe bien dans la liste des tâches
        for enfant, parents in self.precedence.items():
            if enfant not in self.tasks: # Est-ce que l'enfant existe ?
                raise ValueError(f"ERREUR : La tâche '{enfant}' n'existe pas")
            
            for p in parents: # Est-ce que chaque parent existe ?
                if p not in self.tasks:
                    raise ValueError(f"ERREUR : Le parent '{p}' n'existe pas.")

    # 2.4 Validations des entrées (système indéterminé)
    def _check_determinism(self):
        # On compare toutes les tâches deux à deux
        noms = list(self.tasks.keys()) # Liste des tâches
        for i in range(len(noms)):
            for j in range(i + 1, len(noms)):               
                # S'il y a un conflit de Bernstein (Bernstein = True)
                if self.conflict(self.tasks[noms[i]], self.tasks[noms[j]]):
                    # .get() permet d'obtenir les parents, si aucun, ça renvoie []
                    t2_vers_t1 = noms[j] in self.precedence.get(noms[i], []) # t2 est un parent de t1 ?
                    t1_vers_t2 = noms[i] in self.precedence.get(noms[j], []) # t1 est un parent de t2 ?
                    
                    if not (t2_vers_t1 or t1_vers_t2): # Si aucun ordre de priorité
                        raise ValueError(f"ERREUR : Les tâches {noms[i]} et {noms[j]} sont en conflit mais tournent en parallèle. Le système est indéterminé")
    
    # conditions de Bernstein
    def conflict(self, t1, t2):
        if set(t1.writes) & set(t2.reads): # T1 écrit ce que T2 lit
            return True
        if set(t1.reads) & set(t2.writes): # T2 écrit ce que T1 lit
            return True
        if set(t1.writes) & set(t2.writes): # les deux écrivent au même endroit
            return True

        return False

    def _compute_max_parallelism(self):        
        nouveau_graphe = {} # On crée un nouveau dictionnaire pour le graphe optimisé
        for nom in self.tasks: # Pour chaque tâche, on prépare sa liste de successeur
            nouveau_graphe[nom] = [] # Liste vide de successeurs pour chaque tâche
            
        for enfant in self.precedence:
            parents = self.precedence[enfant] # { enfant : [parents] }
            for p in parents: # chaque parent de l'enfant
                if self.conflict(self.tasks[p], self.tasks[enfant]): # parent et enfant dépendant ?
                    nouveau_graphe[p].append(enfant) # Si oui on laisse la flèche parent -> enfant
                    # Si non on casse la flèche, donc on maximise le parallélisme
                    
        return nouveau_graphe

    # 2.6 Test randomisé de déterminisme
    def detTestRnd(self, dico_global):
        # On va faire le test 10 fois pour être sûr
        resultats_trouves = []

        for i in range(10):
            # 1. On donne des valeurs aléatoires aux variables de lecture/écriture
            # On parcourt toutes les tâches pour trouver les variables utilisées
            for nom in self.tasks:
                t = self.tasks[nom]
                toutes_vars = t.reads + t.writes
                for v in toutes_vars:
                    # Si la variable existe dans le dictionnaire global
                    if v in dico_global:
                        # On lui donne un nombre au hasard entre 1 et 100
                        dico_global[v] = random.randint(1, 100)

            # 2. On lance l'exécution parallèle
            self.run()

            # 3. On enregistre l'état final des variables globales
            # On crée une "photo" des valeurs actuelles
            etat_final = {}
            for nom in self.tasks:
                t = self.tasks[nom]
                for v in t.writes:
                    if v in dico_global:
                        etat_final[v] = dico_global[v]
            
            # On ajoute cette "photo" à notre liste de résultats
            resultats_trouves.append(etat_final)

        # 4. On compare : est-ce que les 10 photos sont identiques ?
        premier_resultat = resultats_trouves[0]
        est_determine = True
        
        for r in resultats_trouves:
            if r != premier_resultat:
                est_determine = False
        
        if est_determine == True:
            print("Le test est validé, le système est déterminé (résultats stables).")
        else:
            print("Le système n'est pas déterminé ! Les résultats changent.")

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

    # 2.5 Affichage du système de parallélisme maximal
    def draw(self):
        G = nx.DiGraph(self.max_parallel_graph)
        nx.draw(G, with_labels=True, node_color='lightgreen', node_size=1500)
        plt.show()

    # 2.7 Coût du parallélisme
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
