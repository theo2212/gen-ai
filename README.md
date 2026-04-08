# ⚖️ Legal Agentics AI - Proof of Concept

Bienvenue sur le dépôt du PoC "Legal Agentics AI". Ce projet montre l'intégration d'un LLM Agentique couplé à une base vectorielle RAG et des outils OSINT.

## 🚀 Fonctionnalités Actuelles (Développées)

- **UI Streamlit (Théo)** : Interface Sidebar complète et Layout optimisé. L'utilisateur peut sélectionner son contrat et analyser les résultats dans une grille KPI de type Dashboard. Animation de chargement incluse.
- **Agent LangGraph (Théo & IA)** : Le projet utilise la toute dernière architecture `create_react_agent` avec le modèle hautes performances `llama-3.3-70b-versatile` de Groq.
- **Outil Tavily (Théo)** : L'OSINT est pleinement fonctionnel. Si le LLM détecte une clause d'indexation, il déclenche l'API Tavily pour aller moissonner la valeur de l'INSEE la plus récente et l'affiche dans un JSON formaté.
- **Prompt Expert (Alix/Théo)** : Le System Prompt a été renforcé selon des principes de "Prompt Engineering" avancés. L'IA adopte un persona défini, suit une méthode *Chain Of Thought* en 4 étapes explicites et applique un format de sortie JSON 100% stable.

## 🚧 Ce qui reste à faire (À toi de jouer Hadrien)

La base solide de l'application est en place. Il manque à ce jour la fonction d'interrogation de ChromaDB.
**Hadrien (Engineer 2), voici ta mission :**
1. Tu vas trouver dans le code (`app.py`) une fonction mockée nommée `get_rag_context(contract_name)`.
2. Remplace cette fonction par ta connexion ChromaDB (en conservant la même signature si possible).
3. Au lieu de renvoyer nos faux textes, elle devra requêter ta base vectorielle RAG pour fournir à l'agent juridique le vrai texte issu des *Commercial Lease Agreements* poussés par Alix.

## ⚙️ Installation de l'environnement de développement

1. Créez un environnement virtuel et activez-le :
```bash
python -m venv .venv
# Windows :
.\.venv\Scripts\activate
# Mac/Linux :
source .venv/bin/activate
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Créez votre fichier `.env` sur le modèle du `.env.example` et ajoutez vos clés API :
```text
GROQ_API_KEY=votre_cle
TAVILY_API_KEY=votre_cle
```

4. Lancez l'application :
```bash
streamlit run app.py
```
