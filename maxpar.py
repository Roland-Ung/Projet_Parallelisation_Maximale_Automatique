import threading  # Pour lancer plusieurs fonctions en même temps (parallélisme)
import time       # Pour mesurer le temps
import random     # Pour générer des nombres aléatoires (test de déterminisme)
import networkx as nx  # Pour créer la structure du graphe (les bulles et les flèches)
import matplotlib.pyplot as plt  # Pour afficher le dessin du graphe à l'écran

class Task:
    # Les caractéristiques pour créer une tâche
    def __init__(self, name="", reads=None, writes=None, run=None):
        self.name = name
        if reads == None:
            self.reads = []
        else:
            self.reads = reads
            
        if writes == None:
            self.writes = []
        else:
            self.writes = writes
            
        self.run = run  # La fonction que la tâche doit exécuter

class TaskSystem:

# ----- 2.3 Systèmes de tâches -----

    # Construction d'un système de tâches
    def __init__(self, tasks, precedence_dict):        
        self.tasks = {} # On crée un dictionnaire vide pour ranger les tâches
        for t in tasks:
            if t.name in self.tasks: # On vérifie s'il y a des doublons (2.4 Validation des entrées)
                raise ValueError(f"ERREUR : Le nom de tâche '{t.name}' est dupliqué !")
            self.tasks[t.name] = t # Pour chaque tâche on la range avec son nom (ex: self.tasks["T1"])
            
        self.precedence = precedence_dict # On garde le dictionnaire de précédence
        self._validate_inputs() # On vérifie s'il n'y a pas d'erreurs de noms
        self.max_parallel_graph = self._compute_max_parallelism() # le graphe final (celui optimisé)
        self._check_determinism() # Vérification du déterminisme
    
    # Conditions de Bernstein
    def conflict(self, t1, t2):
        if set(t1.writes) & set(t2.reads): # T1 écrit ce que T2 lit
            return True
        if set(t1.reads) & set(t2.writes): # T2 écrit ce que T1 lit
            return True
        if set(t1.writes) & set(t2.writes): # les deux écrivent au même endroit
            return True

        return False

    # Parallélisation maximale
    def _compute_max_parallelism(self):        
        nouveau_graphe = {} # On crée un nouveau dictionnaire pour le graphe optimisé
        for nom in self.tasks:
            nouveau_graphe[nom] = [] # Liste vide de successeurs pour chaque tâche
            
        for enfant in self.precedence:
            parents = self.precedence[enfant] # { enfant : [parents] }
            for p in parents: # chaque parent de l'enfant
                if self.conflict(self.tasks[p], self.tasks[enfant]): # parent et enfant dépendant ?
                    nouveau_graphe[p].append(enfant) # Si oui on laisse la flèche parent -> enfant
                    # Si non on casse la flèche, donc on maximise le parallélisme
                    
        return nouveau_graphe

    # Dépendances d'une tâche
    def getDependencies(self, nomTache):
        liste_predecesseurs = [] # Tâches qui doivent s'éxécuter avant nomTache
        for parent in self.max_parallel_graph:
            enfants = self.max_parallel_graph[parent]

            if nomTache in enfants: # Si c'est la tâche qu'on cherche
                liste_predecesseurs.append(parent) # On ajoute ses prédécesseurs à la liste
        return liste_predecesseurs

    # Exécution séquentielle
    def runSeq(self):
        G = nx.DiGraph(self.max_parallel_graph) # De dictionnaire à graphe orienté
        ordre = list(nx.topological_sort(G)) # NetworkX analyse le graphe et trouve l'ordre d'éxécution (T1, T2, Somme)
        
        for nom in ordre:
            self.tasks[nom].run() # On lance la fonction de chaque tâche

    # Exécution parallèle
    def run(self):
        G = nx.DiGraph(self.max_parallel_graph)
        deja_fait = [] # Tâches terminées
        a_faire = list(self.tasks.keys()) # (T1, T2, Somme) Tâches restantes
        
        while len(a_faire) > 0: # Tant qu'on n'a pas fini la liste des tâches à faire
            pret_a_lancer = [] # Tâches qui n'ont plus de parents à attendre
            
            # On va voir quels tâches sont prêtes à être lancées (ceux sans parents non terminés)
            for t in a_faire:
                parents = list(G.predecessors(t)) # On récupère les parents de chaque tâche (s'ils en ont)
                tous_finis = True
                for p in parents: # Si aucun parent, pas de boucle
                    if p not in deja_fait:
                        tous_finis = False # Si ce n'est pas encore exécutée, on peut pas lancer la tâche
                
                if tous_finis == True:
                    pret_a_lancer.append(t) # La tâche est prête
            
            threads = []
            for nom in pret_a_lancer:                
                nouveau_thread = threading.Thread(target=self.tasks[nom].run) # On prépare un thread pour lancer la fonction
                threads.append(nouveau_thread)
                nouveau_thread.start() # Le thread exécute la fonction de la tâche, en parallèle
                
            for o in threads: # On attend que tous les threads du groupe finissent
                o.join()
                
            for nom in pret_a_lancer: # Mise à jour des listes
                deja_fait.append(nom)
                a_faire.remove(nom)

# ----- 2.4 Validation des entrées -----

    # Vérification que chaque nom dans les règles existe bien dans la liste des tâches
    def _validate_inputs(self):
        for enfant, parents in self.precedence.items():
            if enfant not in self.tasks: # Est-ce que l'enfant existe ?
                raise ValueError(f"ERREUR : La tâche '{enfant}' n'existe pas")
            
            for p in parents: # Est-ce que chaque parent existe ?
                if p not in self.tasks:
                    raise ValueError(f"ERREUR : Le parent '{p}' n'existe pas.")

    # Vérification du déterminisme (Bernstein et ordre de priorité)
    def _check_determinism(self):
        # On compare toutes les tâches deux à deux
        noms = list(self.tasks.keys()) # Liste des tâches
        for i in range(len(noms)):
            for j in range(i + 1, len(noms)):               
                if self.conflict(self.tasks[noms[i]], self.tasks[noms[j]]):
                    # .get() permet d'obtenir les parents, si aucun, ça renvoie []
                    t2_vers_t1 = noms[j] in self.precedence.get(noms[i], []) # t2 est un parent de t1 ?
                    t1_vers_t2 = noms[i] in self.precedence.get(noms[j], []) # t1 est un parent de t2 ?
                    
                    if not (t2_vers_t1 or t1_vers_t2): # Si aucun ordre de priorité
                        raise ValueError(f"ERREUR : Les tâches {noms[i]} et {noms[j]} sont en conflit mais tournent en parallèle. Le système est indéterminé")

# ----- 2.5 Affichage du système de parallélisme maximal -----

    def draw(self):
        G = nx.DiGraph(self.max_parallel_graph)
        nx.draw(G, with_labels=True, node_color='lightgreen', node_size=1500)
        plt.show()

# ----- 2.6 Test randomisé de déterminisme -----

    def detTestRnd(self, globals):
        for var in globals:
            if isinstance(globals[var], int): # On touche qu'au nombre entier du dictionnaire
                globals[var] = random.randint(0, 100) # On tire des valeurs au sort pour chaque variable entière du dictionnaire (ex: x, y, z)

        etat_initial = globals.copy() # on copie les valeurs aléatoires pour réinitialiser à chaque test
        results = []

        # On teste en lançant le système 5 fois avec les mêmes entrées
        for _ in range(5):
            globals.update(etat_initial) # On remet les valeurs de départ
            self.run() # On lance l'exécution parallèle (les threads)

            # On ne garde que les variables entières (ex: {'X': 10, 'Y': 20})
            final = {k: v for k, v in globals.items() if isinstance(v, int)}
            results.append(final) # On ajoute dans la liste des résultats

        # set() élimine les doublons. S'il n'en reste qu'un, le système est déterminé
        est_determine = len(set(str(r) for r in results)) == 1 # str() transforme dictionnaire -> texte
        
        print(results) # Affichage des résultats
        if est_determine == True:
            print("Le test est validé, le système est déterminé (résultats stables).")
        else:
            print("Le système n'est pas déterminé ! Les résultats changent.")
        
        return est_determine

# ----- 2.7 Coût du parallélisme -----

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
