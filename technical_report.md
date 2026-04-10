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

Le projet a évolué d'une boucle simple à un **système Multi-Agents sophistiqué** orchestré par **LangGraph**. Cette architecture permet de diviser la complexité cognitive en trois rôles spécialisés, chacun opérant comme un nœud dans un graphe d'état :

### 3. Workflow Multi-Agents (LangGraph)
Le système orchestre trois agents spécialisés pour garantir une séparation des responsabilités (Separation of Concerns) :
1.  **Researcher Agent** : Extraction des métriques financières et recherche OSINT (Tavily API) pour l'inflation.
2.  **Compliance Auditor** : Analyse juridique comparative. Cet agent confronte les clauses du bail aux PDF de lois réelles (retrouvés via RAG) pour détecter les clauses abusives.
3.  **Quality Validator** : Contrôle de cohérence, élimination des hallucinations et formatage JSON.

### 4. RAG Engine Multi-Sources & Jurisprudence
Contrairement aux architectures RAG standards, **Contracta.ai** utilise un `MultiSourceRetriever`. Le système est capable de filtrer sa recherche dans deux bases de données distinctes :
*   **Base Contrats** : Le document PDF/TXT chargé par l'utilisateur.
*   **Base Légale (Jurisprudence)** : Une bibliothèque de lois d'États US (Alabama, New York).
L'IA effectue une **analyse de conformité régulatoire** en temps réel en comparant le contrat aux textes législatifs en vigueur dans l'État sélectionné.

**Bénéfice Technique :** Cette spécialisation réduit drastiquement les hallucinations et permet un contrôle granulaire de chaque étape de l'audit juridique.

---

## 3. Stratégie RAG & Gestion Documentaire

### 3.1 Ingestion et Préparation des Données
La fiabilité du système reposant sur la qualité des sources, les contrats ont été prétraités (nettoyage des headers/footers) pour minimiser le bruit.

### 3.2 Stratégie de Chunking (Découpage)
Nous avons implémenté une stratégie de **Recursive Character Splitting** :
- **Taille des blocs (Chunks) :** 1000 caractères.
- **Chevauchement (Overlap) :** 200 caractères.
*Justification Technique :* Dans un bail commercial, une clause complète est généralement comprise entre 500 et 800 caractères. Un segment de 1000 caractères garantit que l'agent dispose de l'intégralité d'une clause. Le chevauchement de 20% évite de scinder des chiffres clés (montant du loyer) entre deux blocs.

### 3.3 Retrieval (Récupération)
Le système utilise une recherche par similarité cosinus pour extraire les **5 morceaux (k=5)** les plus pertinents. Cette valeur a été optimisée pour fournir assez de contexte à l'agent sans saturer sa fenêtre de contexte.

---

## 4. Ingénierie du Prompt (Prompt Engineering)

### 4.1 Persona et Directives
L'agent utilise un prompt système avancé le définissant comme un **"Elite Real Estate Jurist"**. Ce persona impose une rigueur terminologique et un ton professionnel.

### 4.2 Few-Shot Prompting
Pour stabiliser l'extraction JSON, nous avons intégré des exemples de type "Few-Shot". En montrant à l'IA des exemples de contrats bruts suivis de leur analyse JSON parfaite, nous réduisons le taux d'erreur de formatage à quasiment 0%.

---

## 5. Intelligence Agentique & Outils Externes

Contracta.ai se distingue par son utilisation d'outils externes (Function Calling). Lorsque l'agent identifie un besoin de calcul financier ou une recherche d'indexation, il déclenche l'outil **Tavily Search**. 
Exemple : Pour un bail à New York, l'agent récupère en temps réel le taux d'inflation de la Réserve Fédérale pour contextualiser l'augmentation du loyer proposée.

## 6. Expertise Spécifique : "Alix's Shield" & Red Flags
Pour répondre aux exigences pointues d'audit, nous avons intégré un module de détection de **clauses prédatrices** :
- **Unreasonable Termination** : Détection des droits d'expulsion sans motif ou sous préavis < 30 jours.
- **Predatory Acceleration** : Identification des clauses exigeant le solde complet du bail pour un retard mineur (24h).
- **Structural Pass-Through** : Flag automatique des transferts de coûts de structure (toit, fondation) vers le locataire.

## 7. Architecture de Conformité : Le Principe de Précaution
Une innovation majeure de notre solution est la gestion de l'ambiguïté juridique :
*   **Dual-Layer Detection** : L'IA ne se contente pas de chercher des illégalités. Elle identifie les zones de flou ("Grey Areas").
*   **Watchlist Dynamique** : Les clauses suspectes ou peu claires sont isolées dans un onglet dédié, permettant de suggérer des actions correctives (Renégociation, demande de clarification).

---

## 8. Évaluation Critique, Sécurité & Éthique

### 6.1 Suivi des Hallucinations
Un module "Hallucination Tracker" a été développé. Il compare les données extraites au contenu des chunks RAG. Si une information (ex: un montant de loyer) n'est pas littéralement présente dans la source, l'utilisateur est averti.

### 6.2 Résilience aux Injections (Red Teaming)
Nous avons testé le système contre des attaques par injection de prompt (Jailbreak). Le System Prompt est configuré avec des instructions de priorité haute qui empêchent l'agent de sortir de son rôle, même face à des commandes malveillantes ("Ignore previous instructions").

### 6.3 Analyse des Biais
Nous avons identifié que le modèle peut présenter un biais de conservatisme, flaguant comme "abusives" des clauses complexes qui pourraient être légales dans certains états US spécifiques. C'est pourquoi un mode "Human-in-the-loop" (Chatbot interactif) permet à l'expert métier de contester l'IA.

---

## 7. Conclusion
Contracta.ai démontre la viabilité des architectures Agentic RAG pour des cas d'usage industriels complexes. Le système allie la puissance de calcul des LLM modernes à la rigueur de recherche du RAG, offrant une solution robuste de "Copilote Juridique".

---
*(Fin du rapport technique - Version 1.2 - Corporate Standards)*
