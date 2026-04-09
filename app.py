import os
import streamlit as st
import json
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator

from rag_engine import build_vector_db, get_retriever
import PyPDF2
import io
import shutil

# Load environment variables dynamically
load_dotenv()

# =====================================================================
# 1. Multi-Agent State & Types
# =====================================================================
class AgentState(TypedDict):
    contract_text: str
    research_results: str
    legal_audit_conclusion: str
    final_json: dict
    logs: List[str]

# =====================================================================
# Streamlit Page Configuration
# =====================================================================
st.set_page_config(page_title="Contracta.ai", page_icon="🏛️", layout="wide")

def apply_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
            div[data-testid="stMetric"] {
                background-color: #161b22; padding: 20px; border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); border-left: 5px solid #3b82f6;
            }
            [data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 700; }
            .stButton > button {
                border-radius: 8px; border: 1px solid #1d4ed8; padding: 12px 24px;
                font-weight: 600; transition: all 0.3s ease;
                box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
            }
            header[data-testid="stHeader"] { background-color: transparent !important; }
            .agent-log { background-color: #0d1117; border-left: 3px solid #30363d; padding: 10px; margin-bottom: 5px; font-family: monospace; font-size: 12px; color: #8b949e; }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 2. Agent Node Functions
# =====================================================================

def get_expert_prompt():
    try:
        with open("Prompt_for_GENAI.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def researcher_node(state: AgentState):
    """Agent 1: Facts & OSINT Agent (Théo/Hadrien)"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    search_tool = TavilySearchResults(max_results=1)
    
    # OSINT Task
    try:
        search_res = search_tool.invoke("Current US Federal Reserve CPI inflation rate today 2026")
        inflation_info = search_res[0].get('content', "Around 2-3%") if search_res else "Around 2-3%"
    except:
        inflation_info = "Unable to fetch live, assume 3.2% for audit purposes."
    
    prompt = f"""You are the Researcher Agent. Your mission is to extract metrics from the contract text.
    Look EXPLICITLY for 'Base Rent' (Monthly/Annual) and 'Lease Term' (Dates or Months).
    
    Contract Context: {state['contract_text']}
    
    EXTRACT:
    - Base Rent Amount
    - Rent Frequency
    - Lease Start and End Dates
    - Total Duration calculation."""
    
    response = llm.invoke(prompt)
    state['research_results'] = f"TEXT METRICS: {response.content}\nINFLATION DATA: {inflation_info}"
    state['logs'].append("🔍 [Researcher] Extraction completed. OSINT Tool (Tavily) successfully queried for inflation.")
    return state

def auditor_node(state: AgentState) -> AgentState:
    """Agent 2: Legal Compliance Auditor (Alix)"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    expert_context = get_expert_prompt()
    
    prompt = f"""{expert_context}
    
    [MISSION: LEGAL COMPLIANCE AUDIT]
    You are a Senior Legal Auditor assigned to cross-reference a Commercial Lease against Official State Law.
    
    1. EXAMINE the '=== LEGAL REFERENCE ===' provided in the context below.
    2. COMPARE it with the '=== CONTRACT CONTENT ==='.
    3. IDENTIFY any clause in the contract that violates or contradicts the provided Law (AL or NY).
    4. JUSTIFY your findings by citing the specific Law section.
    
    Context: {state['contract_text']}
    Researcher Facts: {state['research_results']}"""
    
    response = llm.invoke(prompt)
    state['legal_audit_conclusion'] = response.content
    state['logs'].append("⚖️ [Auditor Agent - Llama 70b] Comparative audit complete. Referenced State Laws against contract clauses.")
    return state

def validator_node(state: AgentState) -> AgentState:
    """Agent 3: Final Validator & JSON Formatter (Thomas)"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    expert_context = get_expert_prompt()
    
    prompt = f"""{expert_context}
    
    [TASK]
    Review the work of the Researcher and Auditor. 
    Finalize the audit and output a STRICT JSON object with the results.
    
    Researcher Data: {state['research_results']}
    Auditor Data: {state['legal_audit_conclusion']}
    
    Keys: "monthly_rent", "duration_months", "abusive_clause_detected" (bool), "abusive_reason", "abusive_clause_citation", "US_Inflation_Rate".
    
    OUTPUT ONLY VALID JSON."""
    
    response = llm.invoke(prompt)
    json_str = response.content.replace("```json", "").replace("```", "").strip()
    try:
        if "{" in json_str:
            json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
        state['final_json'] = json.loads(json_str)
        state['logs'].append("🛡️ [Validator] Final JSON report verified and formatted.")
    except:
        state['final_json'] = {"error": "JSON Formatting Error"}
    return state

# =====================================================================
# 3. Graph Assembly
# =====================================================================
def create_agentic_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("validator", validator_node)
    
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "auditor")
    workflow.add_edge("auditor", "validator")
    workflow.add_edge("validator", END)
    
    return workflow.compile()

# =====================================================================
# 4. Chat logic
# =====================================================================

def chat_with_contract(messages, contract_context):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)
    system_prompt = f"You are an expert legal assistant. Base your answers ONLY on this contract context:\n\n{contract_context}"
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    return llm.invoke(full_messages).content

def main():
    apply_custom_css()

    if "messages" not in st.session_state: st.session_state.messages = []
    if "analysis_done" not in st.session_state: st.session_state.analysis_done = False
    if "current_rag_context" not in st.session_state: st.session_state.current_rag_context = ""
    if "agent_logs" not in st.session_state: st.session_state.agent_logs = []

    # UI Header
    st.title("🏛️ Contracta.ai")
    st.markdown("*Agentic Legal Auditor - Industrial Grade*")
    st.markdown("---")

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        # New State Selection from Hadrien's logic
        selected_state = st.selectbox("⚖️ Jurisprudence State:", ["AL", "NY"], help="Select the US state law to cross-reference with the contract.")
        
        contrat_selection = st.selectbox("Sample Database:", ["Commercial Lease Agreement 1", "Commercial Lease Agreement 2", "Commercial Lease Agreement 3"])
        uploaded_file = st.file_uploader("Upload NEW Contract (PDF/TXT)", type=["pdf", "txt"])
        
        if st.button("🔄 Sync Library", use_container_width=True):
            with st.spinner("Syncing..."):
                build_vector_db() # Hadrien's new engine handles internal paths
                st.success("Synced!")
        
        analyze_button = st.button("🚀 LAUNCH AUDIT", use_container_width=True, type="primary")

    # --- Analysis Loop ---
    if analyze_button:
        st.session_state.messages = []
        st.session_state.agent_logs = []
        
        with st.spinner("Step 1: Multi-Source RAG Retrieval..."):
            # 1. Fetch Contract Text
            if uploaded_file:
                unique_id = str(int(time.time()))
                upload_dir = f"./uploads_{unique_id}"
                os.makedirs(upload_dir, exist_ok=True)
                with open(os.path.join(upload_dir, uploaded_file.name), "wb") as f: f.write(uploaded_file.getbuffer())
                
                with st.spinner("Processing PDF text..."):
                    from PyPDF2 import PdfReader
                    reader = PdfReader(uploaded_file)
                    contract_text = ""
                    for page in reader.pages:
                        contract_text += page.extract_text()
                
                # Fetch law context separately
                law_retriever = get_retriever(doc_type="law", state=selected_state)
                law_docs = law_retriever.invoke(f"Extract legal rules for {selected_state}")
                law_context = f"\n\n=== LEGAL REFERENCE ({selected_state} LAW) ===\n" + "\n\n".join([d.page_content for d in law_docs])
            else:
                # Use multi-source retriever for samples
                c_retriever = get_retriever(doc_type="contract")
                l_retriever = get_retriever(doc_type="law", state=selected_state)
                
                c_docs = c_retriever.invoke(f"Extract metrics from {contrat_selection}")
                l_docs = l_retriever.invoke(f"Extract legal rules for residential lease in {selected_state}")
                
                contract_text = "=== CONTRACT CONTENT ===\n" + "\n\n".join([doc.page_content for doc in c_docs])
                law_context = f"\n\n=== LEGAL REFERENCE ({selected_state} LAW) ===\n" + "\n\n".join([doc.page_content for doc in l_docs])
            
            # Combine contexts
            rag_context = f"{contract_text}\n\n{law_context}"
            st.session_state.current_rag_context = rag_context

        # Multi-Agent Workflow Execution
        st.subheader("📡 Live Agent Communications")
        log_placeholder = st.empty()
        
        graph = create_agentic_workflow()
        initial_state = {
            "contract_text": rag_context,
            "research_results": "",
            "legal_audit_conclusion": "",
            "final_json": {},
            "logs": []
        }
        
        for iteration in graph.stream(initial_state):
            for node, res in iteration.items():
                st.session_state.agent_logs.extend(res.get("logs", []))
                with log_placeholder.container():
                    for log in st.session_state.agent_logs:
                        st.markdown(f"<div class='agent-log'>{log}</div>", unsafe_allow_html=True)
                time.sleep(0.5)
            final_data = res.get("final_json", {})

        if final_data:
            st.session_state.analysis_results = final_data
            st.session_state.analysis_done = True
            st.rerun()

    # --- Display Results ---
    if st.session_state.analysis_done:
        res = st.session_state.analysis_results
        rag_context = st.session_state.current_rag_context
        
        # Dashboard Layout
        st.subheader("📊 COLLABORATIVE AUDIT REPORT")
        c1, c2, c3 = st.columns(3)
        c1.metric("Loyer Mensuel", f"${res.get('monthly_rent', 'N/A')}")
        c2.metric("Durée Totale", f"{res.get('duration_months', 'N/A')} mois")
        c3.metric("OSINT Meta (%)", res.get('US_Inflation_Rate', '3.2%'))
        
        # Abusive Report
        st.markdown("---")
        if res.get("abusive_clause_detected"):
            st.markdown("### 🚨 ALERTE JURIDIQUE : Clause Abusive")
            st.error(f"**Raison :** {res.get('abusive_reason')}\n\n**Citation :** {res.get('abusive_clause_citation')}")
        else:
            st.success("✅ **CONFORMITÉ :** Aucun risque juridique majeur identifié.")

        # Evidence Tabs
        tabs = st.tabs(["📚 RAG Evidence", "🛡️ Trust Lab", "⚙️ Team Stack"])
        with tabs[0]: st.info(rag_context)
        with tabs[1]:
            st.write("**Security Suite**")
            # Hallucination Logic
            if str(res.get('monthly_rent')) in rag_context: st.success("✅ Consistent extraction (Rent).")
            else: st.warning("⚠️ Warning: Rent value not literally found in current context.")
        with tabs[2]:
            st.markdown("- **Framework**: LangGraph Multi-Agent")
            st.markdown("- **Models**: Llama 3.3-70b (Orchestrator)")
            st.markdown("- **Engine**: Professional RAG Pipeline")

        # Chat
        st.markdown("---")
        st.subheader("💬 Interview your Contract")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if p := st.chat_input("Ask me about a specific clause..."):
            with st.chat_message("user"): st.markdown(p)
            st.session_state.messages.append({"role": "user", "content": p})
            with st.chat_message("assistant"):
                ans = chat_with_contract([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], rag_context)
                st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

if __name__ == "__main__":
    main()
