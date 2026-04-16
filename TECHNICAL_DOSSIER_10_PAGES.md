# CONTRACTA.AI : L'AUDIT JURIDIQUE À L'ÈRE DE L'IA AGENTIQUE
## Dossier d'Architecture & Mémoire Technique
### Masters - Intelligence Artificielle Générative

**Auteurs :** Core Development Team - Legal AI Division  
**Enseignant :** Antoine Palisson  
**Date :** 16 Avril 2026  
**Version :** 3.0 (Édition Étendue - 10 Pages)

---

## 📝 EXECUTIVE SUMMARY (ABSTRACT)

**Contracta.ai** est une solution pionnière d'audit automatisé de baux commerciaux, conçue pour combler le fossé entre la puissance brute des Grands Modèles de Langage (LLM) et la rigueur absolue exigée par le secteur juridique. Ce projet repose sur une architecture **Agentic RAG (Retrieval-Augmented Generation)** opérant via un graphe d'état complexe (**LangGraph**). 

Le système ne se contente pas d'extraire des données ; il met en œuvre une équipe de trois agents spécialisés collaborant pour identifier les clauses prédatrices, vérifier l'indexation des loyers via l'intelligence web (OSINT) et garantir une traçabilité totale via un pipeline de détection des hallucinations. Ce dossier détaille les choix technologiques, les défis de sécurité et la valeur stratégique de Contracta.ai dans un environnement professionnel hautement régulé.

---

## 📖 GLOSSAIRE TECHNIQUE

*   **LLM (Large Language Model) :** Modèle d'intelligence artificielle entraîné sur d'immenses volumes de texte, ici Llama-3.3-70b, capable de raisonnement sémantique.
*   **RAG (Retrieval-Augmented Generation) :** Technique consistant à "nourrir" l'IA de documents spécifiques en temps réel pour éviter les hallucinations et garantir des sources fiables.
*   **Embeddings :** Représentation mathématique (vecteur) d'un texte permettant à l'IA d'en comprendre le sens profond au-delà des simples mots-clés.
*   **Agentique (Agentic) :** Se dit d'une IA capable d'utiliser des outils et de prendre des décisions par elle-même pour accomplir un objectif complexe.
*   **LangGraph :** Framework d'orchestration permettant de définir un flux de travail sous forme de graphe (nœuds et arêtes) avec une gestion d'état persistante.
*   **OSINT (Open Source Intelligence) :** Recherche d'informations dans des sources ouvertes sur internet, ici via l'API Tavily.
*   **ChromaDB :** Base de données vectorielle spécialisée pour stocker et retrouver les segments de documents juridiques.

---

## 🏛️ CHAPITRE 1 : INTRODUCTION & PROBLÉMATIQUE MÉTIER

### 1.1 Le Goulot d'Étranglement du Secteur Juridique
Dans le domaine de l'immobilier commercial, l'audit d'un contrat de bail est une procédure critique. Un document standard peut varier entre 30 et 100 pages, incluant des clauses de loyer escaladées, des responsabilités de maintenance structurelle et des conditions de résiliation souvent cryptiques. Pour un notaire ou un gestionnaire de parc, l'analyse manuelle de ces documents représente un coût opérationnel massif et un risque d'erreur humaine élevé.

### 1.2 Les Faiblesses des IA Classiques
Si l'utilisation de ChatGPT ou d'outils conversationnels simples semble évidente, elle se heurte à trois barrières infranchissables en milieu juridique :
1.  **L'Hallucination :** L'IA peut inventer une clause inexistante ou citer un article de loi erroné.
2.  **L'Opacité :** L'absence de citations directes empêche l'expert humain de valider rapidement l'information.
3.  **L'Isolement Documentaire :** Les LLM standards ont une "date de coupure" de connaissance. Ils ignorent l'inflation actuelle ou les changements récents de jurisprudence.

### 1.3 La Thèse de Contracta.ai
Nous posons l'hypothèse que la fiabilité juridique ne peut être atteinte que par la **spécialisation**. Au lieu de demander à une IA de "Lire le contrat", Contracta.ai propose de "Faire travailler une équipe d'agents". C'est le passage d'une IA passive à une **Intelligence Agentique**.

---

## 🚀 CHAPITRE 2 : VISION STRATÉGIQUE & ARCHITECTURE GLOBALE

### 2.1 La Vision : L'Avocat Augmenté
Contracta.ai n'a pas pour but de remplacer le juriste, mais de lui offrir un "bouclier de conformité". La solution automatise les 95% de tâches répétitives (extraction, vérification de conformité de base) pour permettre à l'humain de se concentrer sur les 5% de négociation stratégique.

### 2.2 Choix du Framework de Raisonnement : LangGraph
Le cœur du système repose sur **LangGraph**. Ce choix est stratégique pour deux raisons :
*   **Directionalité :** Nous imposons un flux de pensée. L'agent chercheur *doit* finir son extraction avant que l'auditeur ne commence son analyse. Cela évite les "sauts de logique".
*   **State Management :** Le système conserve un "Cahier de Liaison" (State) que chaque agent enrichit. C'est la garantie qu'aucune information naine n'est perdue lors du passage de relais.

### 2.3 Stack Technologique : Le Duo de Choc
*   **Groq & Llama-3.3-70b :** Le choix de Groq comme infrastructure permet une latence de réponse quasiment nulle. Pour un audit multi-agents, la vitesse est cruciale pour l'expérience utilisateur. 
*   **Google Gemini Pro Embeddings :** Nous avons sélectionné Gemini pour la partie vectorielle car son modèle d'embeddings est l'un des plus performants au monde pour capturer les nuances des petits caractères juridiques souvent ignorés par d'autres modèles.

---
*(La suite du rapport – Chapitres 3 & 4 – est en cours de rédaction)*
