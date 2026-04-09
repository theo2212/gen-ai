# Architecture Technique : Contracta.ai

Voici le code pour générer ton diagramme d'architecture. Tu peux le copier-coller sur [Mermaid.live](https://mermaid.live/) pour obtenir une image haute définition pour tes slides.

```mermaid
graph TD
    subgraph "Frontend (Streamlit)"
        UI["Interface Utilisateur (Dark Mode)"]
        Chat["Chatbot Interactif"]
    end

    subgraph "RAG Pipeline (Hadrien's Engine)"
        Doc["Document (PDF/TXT)"] --> Split["Chunking (1000 chars / 200 overlap)"]
        Split --> Embed["Gemini Embeddings (Google)"]
        Embed --> DB[("ChromaDB (Vector Base)")]
    end

    subgraph "Agentic Core (LangGraph)"
        Agent["Agent Llama 3.3 (Groq)"]
        Retriever["Retriever (k=5 Chunks)"]
        Tool1["Tavily Search (US Inflation)"]
        
        Agent <--> Retriever
        Agent <--> Tool1
    end

    subgraph "Output & Security"
        JSON["JSON Output (Strict Schema)"]
        Trust["Trust & Security Lab (Hallucination Check)"]
    end

    %% Flow
    UI --> Doc
    DB --> Retriever
    Retriever --> Agent
    Agent --> JSON
    JSON --> UI
    Chat <--> Agent
    Trust -.-> Agent

    %% Styles
    style UI fill:#161b22,stroke:#3b82f6,color:#60a5fa
    style DB fill:#161b22,stroke:#3b82f6,color:#60a5fa
    style Agent fill:#1e4ed8,stroke:#fff,color:#fff
    style Doc fill:#8fa1b4,color:#000
```

## Explications techniques pour tes slides :
1.  **Ingestion (RAG) :** Les documents sont découpés en blocs de 1000 caractères avec un chevauchement de 20%. C'est crucial pour ne pas couper une clause juridique au milieu.
2.  **Stockage :** ChromaDB permet de retrouver les 5 paragraphes les plus pertinents (Similarity Search) pour répondre à une question précise.
3.  **Agent :** L'agent n'est pas passif. Il décide d'utiliser Tavily pour vérifier l'inflation US réelle avant de rendre son verdict.
4.  **Interface :** Streamlit gère le rendu en temps réel et la mémoire de la conversation (Chatbot).
