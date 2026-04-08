import os
import streamlit as st
import json
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Charger dynamiquement les variables d'environnement
load_dotenv()

# =====================================================================
# Configuration de la page Streamlit
# =====================================================================
st.set_page_config(page_title="Contracta.ai", page_icon="🏛️", layout="wide")

# Injection du Design CSS "Premium Corporate"
def apply_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }
            /* Fond de l'application légèrement plus doux */
            .stApp {
                background-color: #f7f9fc;
            }
            /* Design de la Sidebar typé Corporate */
            [data-testid="stSidebar"] {
                background-color: #1a2530;
                background-image: linear-gradient(180deg, #0b131a 0%, #1a2530 100%);
                color: #f0f0f0;
            }
            [data-testid="stSidebar"] * {
                color: #ffffff;
            }
            /* Cartes de KPI (Metrics) avec ombres et bordures */
            div[data-testid="stMetric"] {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
                border-left: 5px solid #2e5b8e;
            }
            [data-testid="stMetricValue"] {
                color: #2e5b8e !important;
                font-weight: 700;
            }
            /* Bouton principal mis en valeur */
            .stButton > button {
                background-color: #2e5b8e !important;
                color: white !important;
                border-radius: 8px;
                border: none;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 16px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 10px rgba(46, 91, 142, 0.2);
            }
            .stButton > button:hover {
                background-color: #173860 !important;
                box-shadow: 0 6px 15px rgba(23, 56, 96, 0.4);
                transform: translateY(-1px);
            }
            /* Titres */
            h1, h2, h3 {
                color: #0b131a;
            }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 1. Fonction Factice de base de données (Mock ChromaDB)
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
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback robuste pour les fichiers txt créés sous Windows (ANSI)
            with open(filename, "r", encoding="windows-1252", errors="replace") as f:
                return f.read()
    return "Erreur : Fichier introuvable."

# =====================================================================
# 2. Logique Agentique (LangChain)
# =====================================================================
def analyze_contract_with_agent(contract_text):
    """
    Fonction qui initialise et exécute l'Agent LangChain avec ChatGroq et Tavily.
    """
    if not os.environ.get("GROQ_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
        st.error("Veuillez configurer les variables d'environnement GROQ_API_KEY et TAVILY_API_KEY avant de lancer l'analyse.")
        st.stop()

    # LLM Groq
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )

    # Outil de recherche Web Tavily
    search_tool = TavilySearchResults(max_results=2)
    tools = [search_tool]

    # Le System Prompt "Expert" (Lecture de Prompt_for_GENAI.txt + OSINT Américain)
    with open("Prompt_for_GENAI.txt", "r", encoding="utf-8") as f:
        alix_prompt = f.read()

    system_message = alix_prompt + """\n
[OSINT Task - IMPERATIVE]
Since this contract falls under US Law without strict rent control, you MUST use the Tavily Search Tool on the internet to find the current "US Federal Reserve Inflation Rate" (or latest US CPI) to evaluate macro-economic context. 
You MUST execute this search and include the found rate in your output JSON under the exact key "US_Inflation_Rate".
"""

    agent_executor = create_react_agent(
        llm, 
        tools, 
        prompt=system_message
    )

    try:
        response = agent_executor.invoke({
            "messages": [HumanMessage(content=f"Voici l'extrait de contrat à analyser :\n\n{contract_text}")]
        })
        return response["messages"][-1].content
    except Exception as e:
        return f"Erreur lors de l'exécution de l'agent : {str(e)}"

# =====================================================================
# 3. Interface Utilisateur Corporate (Streamlit)
# =====================================================================
def main():
    apply_custom_css()

    # En-tête principal
    col_logo, col_titre = st.columns([1, 10])
    with col_logo:
        st.write("")
        st.write("")
        st.markdown("<h1>🏛️</h1>", unsafe_allow_html=True)
    with col_titre:
        st.title("Contracta.ai")
        st.markdown("*Legal Agentics Solution for Notaries & Real Estate Asset Managers*")
    
    st.markdown("---")

    # --- Barre Latérale (Sidebar) ---
    with st.sidebar:
        st.markdown("<h2>🏛️ Contracta.ai</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #8fa1b4; font-size: 14px;'>Legal Agentics Dashboard</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("📄 Base Documentaire")
        
        contrat_selection = st.selectbox(
            "Cible d'analyse :",
            ["Commercial Lease Agreement 1", "Commercial Lease Agreement 2", "Commercial Lease Agreement 3"]
        )
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Bouton d'action massif et explicite
        analyze_button = st.button("🚀 Lancer l'Analyse Agentique", use_container_width=True, type="primary")

    # --- Zone Principale ---
    if analyze_button:
        
        # 1. Récupération du contexte
        rag_context = get_rag_context(contrat_selection)
        
        # 2. Animations Riches (Barre de progression + Spinner)
        st.markdown("### 🤖 Analyse en cours...")
        progress_bar = st.progress(0)
        
        for percent_complete in range(0, 50, 10):
            time.sleep(0.1)
            progress_bar.progress(percent_complete)
            
        with st.spinner("Agent is calling Tavily for current US inflation rates 🇺🇸..."):
            resultat_brut = analyze_contract_with_agent(rag_context)
            progress_bar.progress(100)
            time.sleep(0.3)
            progress_bar.empty()
            
        # 3. Affichage visuel des résultats (KPI et Alertes intelligentes)
        if resultat_brut and "Erreur" not in resultat_brut:
            json_str = resultat_brut.replace("```json", "").replace("```", "").strip()
            
            try:
                donnees_json = json.loads(json_str)
                st.subheader("📊 Rapport d'Audit Financier")
                
                # Métriques Superbes (Loyer / Durée)
                col1, col2 = st.columns(2)
                loyer = donnees_json.get("monthly_rent", "Non trouvé")
                duree = donnees_json.get("duration_months", "Non trouvée")
                col1.metric("Loyer Mensuel", f"{loyer} $" if loyer != "Non trouvé" else loyer)
                col2.metric("Durée du Bail", f"{duree} mois" if duree != "Non trouvée" else duree)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("⚖️ Conclusion Juridique & OSINT")
                
                col3, col4 = st.columns(2)
                
                # Gestion dynamique de l'affichage OSINT (vert/rouge) pour la clause abusive
                abusive_status = donnees_json.get("abusive_clause_detected", False)
                abusive_reason = donnees_json.get("abusive_reason", "Aucune anomalie détectée.")
                
                with col3:
                    if abusive_status == True or str(abusive_status).lower() == "true":
                        st.error(f"**🚨 Clause Abusive Détectée**\n\n{abusive_reason}")
                    else:
                        st.success(f"**✅ Contrat Sain**\n\n{abusive_reason}")
                
                with col4:
                    st.warning(f"**🇺🇸 Taux d'inflation actuel (Agent OSINT) :**\n\n### {donnees_json.get('US_Inflation_Rate', 'Non défini')}")
                
                # Option technique en dessous
                with st.expander("🛠️ Mode Développeur : Voir les données JSON générées"):
                    st.json(donnees_json)
                    
            except json.JSONDecodeError:
                st.error("L'agent n'a pas retourné un JSON parfaitement valide. Voici la réponse brute :")
                st.text(resultat_brut)
        elif "Erreur" in resultat_brut:
            st.error(resultat_brut)

        # 4. Preuve RAG cachée dans un Expander élégant
        st.markdown("---")
        with st.expander("📚 Voir la source documentaire injectée (ChromaDB RAG)"):
            st.markdown("*Le texte ci-dessous correspond au vecteur documentaire récupéré et envoyé au LLM pour le contexte.*")
            st.info(rag_context)

if __name__ == "__main__":
    main()
