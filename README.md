# 🏛️ Contracta.ai - Legal Agentics Solution
**Audit intelligent de baux commerciaux via RAG & Agents IA**

Contracta.ai est un Proof of Concept (PoC) industriel développé pour automatiser et sécuriser l'audit des baux commerciaux pour les notaires et gestionnaires d'actifs.

---

## 🌟 Fonctionnalités Clés

- **Intelligence RAG (Retrieval-Augmented Generation) :** Utilise ChromaDB et les embeddings Gemini pour interroger avec précision une base de contrats PDF/TXT.
- **Agent Juridique Expert :** Propulsé par Llama-3.3-70b (via Groq), l'agent analyse les clauses, extrait les données financières et détecte les clauses abusives.
- **Outils OSINT :** Utilisation de l'API Tavily pour rechercher en temps réel les indices d'inflation (CPI) et contextualiser l'audit.
- **Trust & Security Lab :** Interface intégrée pour vérifier les hallucinations, tester la résilience aux injections de prompt (Red Teaming) et analyser les biais.
- **Chatbot Interactif :** Possibilité de discuter directement avec le contrat pour obtenir des précisions sur des clauses spécifiques.

## 🛠️ Installation & Lancement

1. **Environnement virtuel :**
```bash
python -m venv .venv
# Windows :
.\.venv\Scripts\activate
```

2. **Dépendances :**
```bash
pip install -r requirements.txt
```

3. **Configuration :**
Créez un fichier `.env` à la racine :
```text
GROQ_API_KEY=votre_cle
TAVILY_API_KEY=votre_cle
GOOGLE_API_KEY=votre_cle (pour Gemini Embeddings)
```

4. **Lancement :**
```bash
streamlit run app.py
```

## 🏗️ Architecture Technique
Le projet suit une architecture modulaire :
- `app.py` : Orchestration UI et Logique Agentique.
- `rag_engine.py` : Moteur de recherche vectorielle et gestion ChromaDB.
- `Prompt_for_GENAI.txt` : Expertise juridique encodée via Prompt Engineering (Few-Shot).
- `technical_report.md` : Documentation complète de l'architecture et de la fiabilité.

---
*Projet réalisé dans le cadre du cours de Generative AI - Masters.*
