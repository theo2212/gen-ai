# RAPPORT DE PROJET : CONTRACTA.AI
## Solution d'Agentic RAG pour l'Audit de Baux Commerciaux

**Cours :** Intelligence Artificielle Générative - Masters  
**Enseignant :** Antoine Palisson  
**Date :** 09 Avril 2026  
**Auteurs :** Théo, Hadrien, Alix & Thomas  

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

## 2. Architecture Technique

### 2.1 Stack Technologique
Le choix des outils a été guidé par la performance et la fiabilité (le "80/20 PoC" : maximiser l'impact avec une stack agile).
*   **Modèle de Langage (LLM) :** Llama-3.3-70b via l'infrastructure Groq. Ce choix garantit un raisonnement de haut niveau et des temps de réponse inférieurs à 1 seconde.
*   **Base Vectorielle :** ChromaDB pour la gestion du stockage local des embeddings.
*   **Embeddings :** Google Gemini (`models/gemini-embedding-001`) pour une représentation sémantique fine des termes juridiques.
*   **Framework d'Orchestration :** LangChain & LangGraph pour le chaînage des agents et des outils.
*   **Interface :** Streamlit, offrant une expérience utilisateur fluide en mode sombre (Premium Dark Mode).

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

---

## 6. Évaluation Critique, Sécurité & Éthique

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
*(Fin du rapport technique - Prêt pour conversion DOCX)*
