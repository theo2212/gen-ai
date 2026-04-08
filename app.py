import os
import streamlit as st
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Charger dynamiquement les variables d'environnement du fichier .env
load_dotenv()

# =====================================================================
# Configuration de la page Streamlit
# =====================================================================
st.set_page_config(page_title="Legal Agentics AI", layout="wide")

# =====================================================================
# 1. Fonctions Factices (Mocks) pour la base de données
# =====================================================================
def get_rag_context(contract_name):
    """
    Fonction simulant la récupération RAG (ChromaDB) de Hadrien en lisant le fichier directement.
    """
    file_mapping = {
        "Commercial Lease Agreement 1": "Commercial Lease Agreement_1.txt",
        "Commercial Lease Agreement 2": "Commercial Lease Agreement-2.txt",
        "Commercial Lease Agreement 3": "Commercial Lease Agreement-3.txt",
    }
    filename = file_mapping.get(contract_name)
    if filename and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            # On retourne un extrait significatif ou tout le texte (les modèles Llama-3-70b le gèrent très bien).
            return f.read()
    return "Erreur : Fichier introuvable. Avez-vous copié les fichiers sur le bureau ?"

# =====================================================================
# 2. Logique Agentique (LangChain)
# =====================================================================
def analyze_contract_with_agent(contract_text):
    """
    Fonction qui initialise et exécute l'Agent LangChain avec ChatGroq et Tavily.
    """
    # Vérification de la présence des clés API
    if not os.environ.get("GROQ_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
        st.error("Veuillez configurer les variables d'environnement GROQ_API_KEY et TAVILY_API_KEY avant de lancer l'analyse.")
        st.stop()

    # Initialisation du LLM Groq (modèle mis à jour car l'ancien était décommissionné)
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )

    # Création de l'outil de recherche Tavily
    search_tool = TavilySearchResults(max_results=2)
    tools = [search_tool]

    # Définition du prompt système réclamé par le cahier des charges
    # (Sera remplacé plus tard par le prompt expert d'Alix).
    # Le System Prompt "Expert" (Travail de Business 2 : Fichier injecté dynamiquement)
    with open("Prompt_for_GENAI.txt", "r", encoding="utf-8") as f:
        alix_prompt = f.read()

    system_message = alix_prompt + """\n
[OSINT Task - IMPERATIVE]
Since this contract falls under US Law without strict rent control, you MUST use the Tavily Search Tool on the internet to find the current "US Federal Reserve Inflation Rate" (or latest US CPI) to evaluate macro-economic context. 
You MUST execute this search and include the found rate in your output JSON under the exact key "US_Inflation_Rate".
"""

    # Initialisation de l'agent avec LangGraph (le standard actuel)
    agent_executor = create_react_agent(
        llm, 
        tools, 
        prompt=system_message
    )

    # Exécution de l'agent
    try:
        response = agent_executor.invoke({
            "messages": [HumanMessage(content=f"Voici l'extrait de contrat à analyser :\n\n{contract_text}")]
        })
        # La réponse est dans le dernier message
        return response["messages"][-1].content
    except Exception as e:
        return f"Erreur lors de l'exécution de l'agent : {str(e)}"

# =====================================================================
# 3. Interface Utilisateur (Streamlit)
# =====================================================================
def main():
    st.title("⚖️ Legal Agentics AI")
    st.markdown("Proof of Concept - Analyse des Contrats Locatifs via LLM et OSINT")

    # --- Barre Latérale (Sidebar) ---
    with st.sidebar:
        st.header("🎛️ Commandes")
        
        # Menu déroulant (PAS d'upload de PDF selon cahier des charges)
        contrat_selection = st.selectbox(
            "Sélectionnez le contrat à analyser :",
            ["Commercial Lease Agreement 1", "Commercial Lease Agreement 2", "Commercial Lease Agreement 3"]
        )
        
        # Bouton d'action
        st.markdown("---")
        analyze_button = st.button("Lancer l'analyse", use_container_width=True, type="primary")

    # --- Zone Principale ---
    if analyze_button:
        
        # 1. Récupération du contexte (appel à la fonction mockée)
        rag_context = get_rag_context(contrat_selection)
        
        # 2. Lancement de l'agent avec l'animation OSINT américaine
        with st.spinner("Agent is calling Tavily for current US inflation rates 🇺🇸..."):
            resultat_brut = analyze_contract_with_agent(rag_context)
            
        # 3. Affichage des résultats JSON
        if resultat_brut and "Erreur" not in resultat_brut:
            # Nettoyage rapide (si le LLM ajoute des balises Markdown de code)
            json_str = resultat_brut.replace("```json", "").replace("```", "").strip()
            
            try:
                donnees_json = json.loads(json_str)
                st.subheader("📑 Résultats de l'extraction")
                
                # Affichage sous forme de vue table / métriques (propre)
                col1, col2 = st.columns(2)
                col1.metric("Loyer Mensuel", donnees_json.get("monthly_rent", "Non trouvé"))
                col2.metric("Durée du Bail", donnees_json.get("duration_months", "Non trouvée"))
                
                col3, col4 = st.columns(2)
                abusive_status = str(donnees_json.get("abusive_clause_detected", "Non trouvé"))
                abusive_reason = str(donnees_json.get("abusive_reason", ""))
                col3.info(f"**Clause abusive détectée :**\n{abusive_status} - {abusive_reason}")
                col4.warning(f"**Taux d'inflation actuel (US) via OSINT :**\n{donnees_json.get('US_Inflation_Rate', 'Non défini')}")
                
                # Option technique : le JSON Brut
                with st.expander("Voir les données brutes (JSON)"):
                    st.json(donnees_json)
                    
            except json.JSONDecodeError:
                st.error("L'agent n'a pas retourné un JSON parfaitement valide. Voici la réponse brute :")
                st.text(resultat_brut)
        elif "Erreur" in resultat_brut:
            st.error(resultat_brut)

        # 4. Affichage de la preuve de provenance (Preuve RAG)
        st.markdown("---")
        st.subheader("🔎 Preuve RAG")
        st.caption("Extrait de la source ayant été fournie au LLM (Base Vectorielle ChromaDB)")
        st.info(rag_context)

if __name__ == "__main__":
    main()
