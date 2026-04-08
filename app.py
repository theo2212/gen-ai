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
    Fonction factice simulant la récupération de contexte depuis ChromaDB.
    À remplacer ultérieurement par la VRAIE fonction de Hadrien (Engineer 2).
    """
    mocks = {
        "Contrat Skema A": "Article 1: Le loyer mensuel est fixé à 1500 euros.\nArticle 2: La durée du bail est de 36 mois.\nArticle 3: Le présent contrat inclut une clause d'indexation basée sur l'IRL.",
        "Contrat Skema B": "Bail commercial.\nLoyer: 800 euros/mois.\nDurée: 12 mois.\nAucune clause spécifique d'indexation n'est mentionnée.",
        "Contrat Skema C": "Contrat de location.\nLoyer: 2500 euros.\nDurée: 24 mois.\nClause d'indexation annuelle présente.\nClause additionnelle : Le locataire devra s'acquitter de toutes les réparations structurelles du bâtiment (clause suspectée abusive)."
    }
    return mocks.get(contract_name, "Aucun contexte trouvé pour ce contrat.")

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
    # Le System Prompt "Expert" (Travail de Business 2)
    system_message = """Tu es "Legal Agentics AI", un avocat digital ultra-qualifié spécialisé en droit des baux commerciaux internationaux et français.
Ta mission stricte est d'analyser des contrats de bail complexes et d'extraire la grille financière et de risque légal.

Voici ta méthode de raisonnement étape par étape :
Étape 1 - Loyer : Repère la section "Rent" ou "Base Rent". Isole le loyer MENSUEL. Ne le confonds pas avec le "Security Deposit". Si le loyer est annuel, donne son équivalent mensuel.
Étape 2 - Durée : Identifie les dates dans la section "Term" ou "Durée". Convertis toujours cette durée calendaire en MOIS. Ex: 5 ans = 60 mois.
Étape 3 - Audit des clauses abusives : L'équilibre contractuel est fondamental. Analyse minutieusement la répartition des charges ("Utilities", "Repairs", "Insurance", "Taxes"). Si le contrat impose au locataire (Tenant) de payer ou d'assurer des "réparations structurelles" du bâtiment (Structural components) qui reviennent normalement au propriétaire, marque cette clause comme POTENTIELLEMENT ABUSIVE. Réponds par "Oui" ou "Non" suivi d'une courte preuve.
Étape 4 - Enquête OSINT sur l'Indexation : Cherche toute mention relative à la révision du loyer ("Indexation", "Inflation", "IRL").
👉 RÈGLE ABSOLUE : Si une telle clause est détectée, tu AS L'OBLIGATION d'utiliser ton outil externe (Tavily Search) pour chercher sur Internet "Indice de Référence des Loyers INSEE 2026" (ou la dernière valeur officielle la plus récente).
👉 RÈGLE ABSOLUE : S'il n'y a pas d'indexation, écris "Non applicable".

Format de sortie strict : RIEN D'AUTRE QU'UN BLOC JSON PARFAITEMENT VALIDE.
{
    "Loyer mensuel": "...",
    "Durée en mois": "...",
    "Présence de clause abusive": "Oui/Non - [Brève explication]",
    "IRL 2026": "..."
}"""

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
            ["Contrat Skema A", "Contrat Skema B", "Contrat Skema C"]
        )
        
        # Bouton d'action
        st.markdown("---")
        analyze_button = st.button("Lancer l'analyse", use_container_width=True, type="primary")

    # --- Zone Principale ---
    if analyze_button:
        
        # 1. Récupération du contexte (appel à la fonction mockée)
        rag_context = get_rag_context(contrat_selection)
        
        # 2. Lancement de l'agent avec l'animation imposée
        with st.spinner("Agent is searching INSEE for current inflation rates..."):
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
                col1.metric("Loyer Mensuel", donnees_json.get("Loyer mensuel", "Non trouvé"))
                col2.metric("Durée du Bail", donnees_json.get("Durée en mois", "Non trouvée"))
                
                col3, col4 = st.columns(2)
                col3.info(f"**Clause abusive détectée :**\n{donnees_json.get('Présence de clause abusive', 'Information non trouvée')}")
                col4.warning(f"**Indice de Référence des Loyers (IRL) 2026 :**\n{donnees_json.get('IRL 2026', 'Non défini')}")
                
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
