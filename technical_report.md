# RAPPORT DE PROJET : CONTRACTA.AI
## Solution d'Agentic RAG pour l'Audit de Baux Commerciaux

**Cours :** Intelligence Artificielle Générative - Masters  
**Enseignant :** Antoine Palisson  
**Date :** 09 Avril 2026  
**Auteurs :** Core Development Team - Legal AI Division  

---

## 1. Introduction & Objectifs du Projet

### 1.1 Contexte Professionnel
Dans le secteur de l'immobilier d'entreprise et du notariat, l'audit de contrats de bail commercial est une tâche critique mais extrêmement chronophage. Un bail standard peut compter plus de 50 pages de clauses techniques, financières et juridiques. L'erreur humaine lors de l'extraction de données ou de l'identification de clauses abusives représente un risque financier majeur.

### 1.2 La Solution Contracta.ai
Contracta.ai est une plateforme d'IA spécialisée qui automatise ce processus. Contrairement à un simple chatbot, il s'agit d'un **système agentique** capable de :
1.  **Lire et indexer** des contrats via une architecture RAG (Retrieval-Augmented Generation).
2.  **Extraire** avec précision des données structurées (Loyer, Durée).
3.  **Analyser** la légalité des clauses selon la jurisprudence.
4.  **Rechercher** des informations contextuelles externes (Inflation US CPI via Tavily).

---

## 2. Choix d'Architecture : Système Multi-Agents Collaboratif

Le projet utilise un **système Multi-Agents sophistiqué** orchestré par **LangGraph**. Cette architecture permet de diviser la complexité cognitive en trois rôles spécialisés, chacun opérant comme un nœud dans un graphe d'état :

### 3. Workflow Multi-Agents (LangGraph)
Le système orchestre trois agents spécialisés utilisant le modèle **Llama-3.3-70b-versatile** via Groq pour garantir une puissance de calcul maximale et une latence minimale :

1.  **Researcher Agent** : Extrait les métriques financières du contrat. Il utilise le **Function Calling** pour lancer des recherches **Tavily API** en temps réel, permettant de récupérer des données macro-économiques (CPI) non présentes dans ses données d'entraînement.
2.  **Compliance Auditor** : Réalise l'analyse juridique comparative. Il confronte les clauses extraites aux lois d'États (Alabama/NY) stockées localement dans l'application. Le modèle utilise ici un prompt de type "Juriste Expert" pour éviter les omissions.
3.  **Quality Validator** : Agit comme le superviseur final. Il contrôle la cohérence, élimine les hallucinations et formate le rapport en **JSON strict**. Il gère également le **Chatbot interactif**, en accédant dynamiquement au contexte RAG pour répondre aux questions spécifiques du client avec une traçabilité totale (sections citées).

### 4. RAG Engine Multi-Sources & Jurisprudence
Contrairement aux architectures RAG standards, **Contracta.ai** utilise un `MultiSourceRetriever`. Le système est capable de filtrer sa recherche dans deux bases de données distinctes :
*   **Base Contrat** : Le document PDF chargé par l'utilisateur.
*   **Base Légale (Jurisprudence)** : Une bibliothèque locale de lois.
Le système sélectionne automatiquement la bonne base de connaissances grâce aux métadonnées injectées dans le prompt, garantissant que l'audit d'un bail à New York ne se réfère pas par erreur aux lois de l'Alabama.

---

## 3. Stratégie RAG & Gestion Documentaire

### 3.1 Ingestion et Préparation des Données
La fiabilité du système reposant sur la qualité des sources, les contrats ont été prétraités pour minimiser le bruit. Nous utilisons **Google Gemini-1.0-Pro-Embeddings** pour la vectorisation, offrant une compréhension profonde des concepts légaux.

### 3.2 Stratégie de Chunking (Découpage)
Nous avons implémenté une stratégie de **Recursive Character Splitting** :
- **Taille des blocs (Chunks) :** 1000 caractères.
- **Chevauchement (Overlap) :** 200 caractères.
*Justification Technique :* Cela garantit qu'une clause complète n'est pas coupée en deux, assurant que le modèle dispose toujours du contexte entier pour juger de la légalité d'un article.

### 3.3 Retrieval (Récupération)
Le système utilise une recherche par **similarité cosinus** pour extraire les **5 blocs (k=5)** les plus pertinents. Des tests internes ont montré que ce paramètre offrait le meilleur compromis entre richesse du contexte et saturation de la fenêtre d'attention du modèle.

---

## 4. Ingénierie du Prompt (Prompt Engineering)

### 4.1 Persona et Température
L'agent utilise un prompt système le définissant comme un **"Elite Real Estate Jurist"**. La **température est fixée à 0.0** pour l'audit (pour garantir la répétabilité et la précision) et à **0.3 pour le chat** (pour une interaction plus naturelle).

### 4.2 Few-Shot Prompting
Pour stabiliser l'extraction JSON, nous avons intégré des exemples de type "Few-Shot". Cela force le modèle à suivre un schéma strict, réduisant le taux d'erreur de formatage à quasiment 0%.

---

## 5. Expertise Spécifique : "Alix's Shield" & Red Flags
Nous avons intégré un module de détection de **clauses prédatrices** :
- **Unreasonable Termination** : Détection des droits d'expulsion abusifs.
- **Predatory Acceleration** : Identification des pénalités de retard excessives.
- **Structural Pass-Through** : Flag des transferts de coûts de structure.
Ce "Shield" repose sur le bon sens juridique et peut être étendu en langage naturel par des experts métiers pour couvrir de nouvelles régulations.

---

## 6. Sécurité, Évaluation & Éthique

### 6.1 Résilience et Hallucination Tracking
Un module "Hallucination Tracker" compare les données extraites au contenu source. Si une information n'est pas littéralement présente dans le contrat, l'utilisateur reçoit une alerte de confiance basse.

### 6.2 Red Teaming
Le système a été testé contre des attaques par **Injection de Prompt** et **RAG Poisoning**. Pour mitiger ces risques, nous utilisons des **délimiteurs XML** et une sanitisation stricte des entrées utilisateurs, empêchant le détournement de la mission de l'agent.

---

## 7. Conclusion
Contracta.ai démontre la viabilité des architectures **Agentic RAG**. Le système allie la puissance de calcul des LLM modernes à la rigueur de recherche du RAG, offrant une traçabilité parfaite et une solution robuste pour les métiers à forte régulation.

---
*(Fin du rapport technique - Version Finale validée - Corporate & Safety Standardized)*
