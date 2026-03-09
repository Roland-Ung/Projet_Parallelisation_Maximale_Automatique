import threading  # Importe le module pour gérer l'exécution de plusieurs tâches en même temps (threads)
import time       # Importe le module pour mesurer le temps d'exécution ou faire des pauses
import random     # Importe le module pour générer des nombres aléatoires (utile pour les tests)
import copy       # Importe le module pour copier des objets (utile pour ne pas modifier l'original)
import networkx as nx  # Bibliothèque pour créer, manipuler et étudier les réseaux/graphes
import matplotlib.pyplot as plt  # Bibliothèque pour afficher des graphiques et dessiner le graphe

class Task:
    # Le constructeur de la classe Task (définit ce qu'est une tâche)
    def __init__(self, name="", reads=None, writes=None, run=None):
        self.name = name  # Nom de la tâche (ex: "T1")
        self.reads = reads if reads else []  # Liste des variables lues par la tâche
        self.writes = writes if writes else []  # Liste des variables modifiées par la tâche
        self.run = run  # La fonction réelle (le code Python) que la tâche doit exécuter

class TaskSystem:
    # Le constructeur du système (prend une liste de tâches et un dictionnaire de précédence)
    def __init__(self, tasks, precedence_dict):
        # Transforme la liste de tâches en dictionnaire {nom: objet} pour les retrouver facilement
        self.tasks = {t.name: t for t in tasks}
        # Stocke les contraintes d'ordre de départ données par l'utilisateur
        self.precedence = precedence_dict
        # Appelle la méthode pour vérifier que les entrées sont correctes (pas d'erreurs de noms)
        self._validate_inputs()
        # Calcule le graphe final en appliquant les conditions de Bernstein
        self.max_parallel_graph = self._compute_max_parallelism()

    def _validate_inputs(self):
        # Vérifie si le nombre de noms uniques correspond au nombre de tâches (détection de doublons)
        if len(self.tasks) != len(set(self.tasks.keys())):
            raise ValueError("Erreur : Les noms de tâches doivent être uniques.")
        # Parcourt chaque tâche déclarée dans le dictionnaire de précédence
        for task_name, deps in self.precedence.items():
            # Si le nom de la tâche n'existe pas dans la liste fournie au départ
            if task_name not in self.tasks:
                raise ValueError(f"Tâche {task_name} dans le dictionnaire de précédence inexistante.")
            # Pour chaque dépendance (tâche parente) de cette tâche
            for dep in deps:
                # Si le nom de la dépendance n'existe pas dans la liste des tâches
                if dep not in self.tasks:
                    raise ValueError(f"Dépendance {dep} inexistante pour la tâche {task_name}.")

    def _bernstein(self, t1_name, t2_name):
        """Vérifie si deux tâches interfèrent selon les conditions de Bernstein."""
        t1, t2 = self.tasks[t1_name], self.tasks[t2_name]  # Récupère les deux objets Task à comparer
        i1, o1 = set(t1.reads), set(t1.writes)  # Définit les ensembles de lecture (Input) et écriture (Output) de T1
        i2, o2 = set(t2.reads), set(t2.writes)  # Définit les ensembles de lecture (Input) et écriture (Output) de T2
        
        # Condition 1: T1 écrit dans une variable lue par T2 (o1 ∩ i2)
        # Condition 2: T2 écrit dans une variable lue par T1 (o2 ∩ i1)
        # Condition 3: Les deux écrivent dans la même variable (o1 ∩ o2)
        # .isdisjoint() renvoie True si l'intersection est vide. On veut que les trois soient vides.
        interfere = not (i1.isdisjoint(o2) and o1.isdisjoint(i2) and o1.isdisjoint(o2))
        return interfere  # Renvoie True si elles sont en conflit, False sinon

    def _compute_max_parallelism(self):
        """Construit le graphe de parallélisme maximal."""
        # Initialise un dictionnaire d'adjacence vide pour chaque tâche {Nom: [Enfants]}
        adj = {name: [] for name in self.tasks}
        # Parcourt chaque tâche et ses dépendances imposées par l'utilisateur
        for task, deps in self.precedence.items():
            for dep in deps:
                # On ne garde la contrainte d'ordre QUE si Bernstein dit qu'elles interfèrent
                if self._bernstein(task, dep):
                    # dep doit s'exécuter avant task, on ajoute donc task à la liste des successeurs de dep
                    adj[dep].append(task)
        return adj  # Retourne le graphe optimisé

    def getDependencies(self, nomTache):
        """Renvoie la liste des tâches qui doivent s'exécuter avant la tâche donnée."""
        deps = []  # Liste pour stocker les parents trouvés
        # Parcourt le graphe (parent -> liste d'enfants)
        for parent, children in self.max_parallel_graph.items():
            # Si notre tâche cible est dans la liste des enfants d'un parent
            if nomTache in children:
                deps.append(parent)  # On ajoute ce parent à la liste
        return deps  # Retourne la liste des prédécesseurs

    def runSeq(self):
        """Exécute les tâches l'une après l'autre en respectant l'ordre logique."""
        G = nx.DiGraph(self.max_parallel_graph)  # Convertit notre dictionnaire en graphe NetworkX
        order = list(nx.topological_sort(G))  # Calcule un ordre séquentiel valide (tri topologique)
        for name in order:  # Pour chaque nom de tâche dans l'ordre calculé
            self.tasks[name].run()  # Appelle la fonction de la tâche

    def run(self):
        """Exécute les tâches en parallèle dès que possible via des threads."""
        G = nx.DiGraph(self.max_parallel_graph)  # Utilise NetworkX pour manipuler le graphe
        executed = set()  # Ensemble pour suivre les tâches terminées
        to_execute = set(self.tasks.keys())  # Ensemble des tâches qu'il reste à faire
        
        while to_execute:  # Tant qu'il reste des tâches non terminées
            # Trouve les tâches dont TOUS les parents ont déjà été exécutés
            ready = [t for t in to_execute if all(p in executed for p in G.predecessors(t))]
            threads = []  # Liste pour stocker les threads de l'étape actuelle
            for t_name in ready:  # Pour chaque tâche prête à être lancée
                # Crée un nouveau thread qui exécutera la fonction 'run' de la tâche
                thread = threading.Thread(target=self.tasks[t_name].run)
                threads.append(thread)  # Ajoute le thread à la liste
                thread.start()  # Démarre l'exécution du thread immédiatement
            
            for thread in threads:  # Pour chaque thread lancé dans ce cycle
                thread.join()  # Attend que le thread se termine avant de passer à la suite
            
            for t_name in ready:  # Une fois les threads terminés
                executed.add(t_name)  # Marque la tâche comme terminée
                to_execute.remove(t_name)  # L'enlève de la liste des tâches à faire

    def draw(self):
        """Affiche le graphe de précédence sous forme de schéma."""
        G = nx.DiGraph(self.max_parallel_graph)  # Crée l'objet graphe dirigé
        pos = nx.spring_layout(G)  # Calcule une disposition esthétique des nœuds
        # Dessine le graphe avec des étiquettes, une couleur bleue, et des flèches
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_weight='bold', arrows=True)
        plt.show()  # Ouvre la fenêtre d'affichage du dessin

    def parCost(self, iterations=5):
        """Compare les performances entre le mode séquentiel et parallèle."""
        self.runSeq()  # Exécution de "chauffe" pour préparer le processeur/cache
        
        t_seq_total = 0  # Initialise le compteur de temps pour le séquentiel
        for _ in range(iterations):  # Répète l'opération plusieurs fois
            start = time.time()  # Capture l'heure précise de début
            self.runSeq()  # Exécute en séquentiel
            t_seq_total += (time.time() - start)  # Ajoute la durée écoulée au total
            
        t_par_total = 0  # Initialise le compteur de temps pour le parallèle
        for _ in range(iterations):  # Répète l'opération plusieurs fois
            start = time.time()  # Capture l'heure précise de début
            self.run()  # Exécute en parallèle
            t_par_total += (time.time() - start)  # Ajoute la durée écoulée au total
            
        # Affiche les moyennes de temps calculées
        print(f"Moyenne Séquentielle : {t_seq_total/iterations:.5f}s")
        print(f"Moyenne Parallèle   : {t_par_total/iterations:.5f}s")