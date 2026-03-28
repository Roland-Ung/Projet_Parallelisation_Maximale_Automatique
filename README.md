# Projet_Parallelisation_maximale_automatique

## Objectifs
- Obtenir le système de tâches de parallélisme maximal réunissant les tâches en entrée
- Exécuter le système de tâches de façon séquentielle, tout en respectant les contraintes de précédence
- Exécuter le système de tâches en parallèle, tout en respectant les contraintes de précédence

## Fonctionnalités
### 1 - Analyse de Dépendances
- Implémentation des conditions de Bernstein pour détecter les conflits de lecture/écriture.

### 2 - Génération de Graphe
- Création automatique d'un graphe de précédence optimisé avec NetworkX.

### 3 - Ordonnancement Parallèle
- Moteur d'exécution utilisant threading pour maximiser l'usage du CPU.

### 4 - Garantie de Déterminisme
- Test de robustesse (detTestRnd) pour prouver que le parallélisme ne corrompt pas les données.

### 5 - Analyse de Performance
- Comparaison statistique entre exécution séquentielle et parallèle.

### 6 - Visualisation
- Affichage graphique du réseau de tâches.

## Utilisation

### Clôner le dépôt
```bash
git clone https://github.com/Roland-Ung/Projet_Parallelisation_Maximale_Automatique.git
cd Projet_Parallelisation_Maximale_Automatique
```

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Lancer le test
```bash
python test_projet.py
```

## Structure du projet
```
Projet_Parallelisation_Maximale_Automatique/
│
├── test_projet.py       Fichier de test
├── maxpar.py            Bibliothèque : fonctionnalités sous forme de classes et de fonctions publiques
├── .gitignore           Fichiers à exclure de Git
├── requirements.txt     Liste des dépendances Python
└── README.md
```
