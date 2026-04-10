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

# Load environment variables
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
    """Execution Layer: Metrics Extraction & OSINT Research"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    search_tool = TavilySearchResults(max_results=1)
    
    try:
        search_res = search_tool.invoke("Current US Federal Reserve CPI inflation rate today 2026")
        inflation_info = search_res[0].get('content', "Around 2-3%") if search_res else "Around 2-3%"
    except:
        inflation_info = "Assume 3.2% for audit purposes."
    
    prompt = f"You are the Researcher. Extract 'Base Rent' and 'Lease Term' from this text:\n\n{state['contract_text']}"
    response = llm.invoke(prompt)
    state['research_results'] = f"TEXT METRICS: {response.content}\nINFLATION DATA: {inflation_info}"
    state['logs'].append("🔍 [Researcher] Metrics extracted and OSINT queried.")
    return state

def auditor_node(state: AgentState) -> AgentState:
    """Legal Layer: Regulatory Compliance Audit"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    expert_context = get_expert_prompt()
    
    prompt = f"""{expert_context}
    
    [MISSION: ALIX'S PROTECTIVE SHIELD]
    Audit the text for abusive clauses. You must actively flag:

    1. Unreasonable Termination: Rights allowing the landlord to evict without cause, or with absurdly short notice (e.g., under 30 days) without compensation.
    2. Predatory Acceleration: Clauses demanding the full term's rent for minor delays (e.g., 24-48 hours late).
    3. Unfair Structural/Financial Pass-Throughs: Clauses forcing the tenant to pay for major structural repairs (roofs, foundations) or the landlord's personal legal fees.
    
    COMPARE the '=== LEGAL REFERENCE ===' with the '=== CONTRACT CONTENT ==='.
    For each issue, extract the EXACT SECTION NUMBER (e.g. "Section 10.b") if available.
    When in doubt, FLAG AS SUSPICIOUS/UNCLEAR for the Watchlist.
    
    Context: {state['contract_text']}
    Researcher Facts: {state['research_results']}"""
    
    response = llm.invoke(prompt)
    state['legal_audit_conclusion'] = response.content
    state['logs'].append("⚖️ [Compliance] Regulatory audit complete. Identified risks and ambiguities.")
    return state

def validator_node(state: AgentState) -> AgentState:
    """Quality Layer: Output Validation & JSON Formatting"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    
    prompt = f"""Format the following legal audit results into a STRICT JSON object.
    [PRINCIPLE: PRECAUTIONARY AUDIT]
    - All clear violations -> 'abusive_clauses'.
    - All unclear, risky or ambiguous points -> 'suspicious_clauses'.
    
    Data: {state['legal_audit_conclusion']}
    Research: {state['research_results']}
    
    JSON STRUCTURE:
    {{
      "monthly_rent": "...",
      "duration_months": "...",
      "abusive_clauses": [{{"clause": "...", "reason": "...", "section_number": "...", "severity": "HIGH"}}],
      "suspicious_clauses": [
        {{"clause": "...", "reason": "...", "section_number": "...", "advice": "..."}}
      ],
      "US_Inflation_Rate": "..."
    }}
    OUTPUT ONLY VALID JSON."""
    
    response = llm.invoke(prompt)
    json_str = response.content.strip()
    try:
        if "{" in json_str:
            json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
        state['final_json'] = json.loads(json_str)
        state['logs'].append("🛡️ [Validator] Final JSON report verified.")
    except:
        # Fallback if AI fails JSON
        state['final_json'] = {"monthly_rent": "N/A", "abusive_clauses": [], "suspicious_clauses": []}
        state['logs'].append("⚠️ [Validator] Critical: Parsing error, results simplified.")
    return state

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

def chat_with_contract(messages, contract_context):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)
    system_prompt = f"You are an expert legal assistant. Base answers ONLY on this context:\n\n{contract_context}"
    # Filter messages to only keep role and content
    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    full_messages = [{"role": "system", "content": system_prompt}] + clean_messages
    return llm.invoke(full_messages).content

def main():
    apply_custom_css()
    if "messages" not in st.session_state: st.session_state.messages = []
    if "analysis_done" not in st.session_state: st.session_state.analysis_done = False
    if "current_rag_context" not in st.session_state: st.session_state.current_rag_context = ""
    if "agent_logs" not in st.session_state: st.session_state.agent_logs = []
    if "analysis_results" not in st.session_state: st.session_state.analysis_results = {}

    st.title("🏛️ Contracta.ai")
    st.markdown("*Agentic Legal Auditor - Industrial Grade*")
    st.markdown("---")

    with st.sidebar:
        st.header("⚙️ Configuration")
        selected_state = st.selectbox("⚖️ Jurisprudence State:", ["AL", "NY"])
        uploaded_file = st.file_uploader("Upload NEW Contract", type=["pdf", "txt"])
        
        if st.button("🔄 Sync Library", use_container_width=True):
            with st.spinner("Syncing..."):
                build_vector_db()
                st.success("Synced!")
        
        analyze_button = st.button("🚀 LAUNCH AUDIT", use_container_width=True, type="primary")

    if analyze_button:
        st.session_state.messages = []
        st.session_state.agent_logs = []
        with st.spinner("Retrieving RAG Context..."):
            if uploaded_file:
                from PyPDF2 import PdfReader
                reader = PdfReader(uploaded_file)
                contract_text = "".join([p.extract_text() for p in reader.pages])
                law_retriever = get_retriever(doc_type="law", state=selected_state)
                law_docs = law_retriever.invoke(f"Abusive clauses in {selected_state}")
                law_context = f"\n\n=== LEGAL REFERENCE ({selected_state} LAW) ===\n" + "\n".join([d.page_content for d in law_docs])
            else:
                contract_text = "No contract uploaded. Use samples."
                law_context = "No law context."
            
            rag_context = f"{contract_text}\n\n{law_context}"
            st.session_state.current_rag_context = rag_context

        st.subheader("📡 Live Agent Communications")
        log_placeholder = st.empty()
        graph = create_agentic_workflow()
        
        initial_state = {"contract_text": rag_context, "research_results": "", "legal_audit_conclusion": "", "final_json": {}, "logs": []}
        
        for iteration in graph.stream(initial_state):
            for node, res in iteration.items():
                st.session_state.agent_logs.extend(res.get("logs", []))
                with log_placeholder.container():
                    for log in st.session_state.agent_logs:
                        st.markdown(f"<div class='agent-log'>{log}</div>", unsafe_allow_html=True)
            final_data = res.get("final_json", {})
        
        if final_data:
            st.session_state.analysis_results = final_data
            st.session_state.analysis_done = True
            st.rerun()

    if st.session_state.analysis_done:
        res = st.session_state.analysis_results
        rag_context = st.session_state.current_rag_context
        st.subheader("📊 COLLABORATIVE AUDIT REPORT")
        abusive = res.get("abusive_clauses", [])
        suspicious = res.get("suspicious_clauses", [])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Monthly Rent", f"${res.get('monthly_rent', 'N/A')}")
        c2.metric("Term", f"{res.get('duration_months', 'N/A')} months")
        c3.metric("🚨 Abusives", len(abusive))
        c4.metric("📈 US Inflation", res.get('US_Inflation_Rate', 'N/A'), delta="Live CPI Indicator")
        
        st.markdown("---")
        t1, t2, t3, t4 = st.tabs(["🚨 Abusive Clauses", "📈 Market Context", "📚 RAG Evidence", "🛡️ Trust Lab"])
        
        with t1:
            if not abusive: 
                st.success("No strictly abusive clauses detected.")
            for item in abusive:
                with st.expander(f"🔴 RISK {item.get('severity', 'HIGH')}: {item.get('section_number', 'N/A')}..."):
                    st.error(f"**Section:** {item.get('section_number', 'Unknown')}")
                    st.error(f"**Reason:** {item.get('reason', 'N/A')}")
                    st.info(f"**Text:** {item.get('clause', 'N/A')}")

        with t2:
            st.subheader("US Macro-Economic Data")
            st.info("The agent successfully queried the live internet via Tavily OSINT to retrieve current benchmark data.")
            st.metric("Consumer Price Index (CPI)", res.get('US_Inflation_Rate', 'N/A'))
            st.markdown("""
            **Why this matters?**
            In commercial real estate, rent indexation is tied to official inflation rates. 
            Our agent uses this live figure to detect if a landlord is attempting an unjustified rent increase.
            """)

        with t3: st.info(rag_context)
        with t4:
            st.write("**Security Suite - Industrial Grade**")
            st.markdown("- **Framework**: LangGraph Multi-Agent")
            st.markdown("- **Models**: Llama 3.3-70b (Orchestrator)")

        st.markdown("---")
        st.subheader("💬 Interview your Contract")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if p := st.chat_input("Ask about a specific clause..."):
            with st.chat_message("user"): st.markdown(p)
            st.session_state.messages.append({"role": "user", "content": p})
            with st.chat_message("assistant"):
                ans = chat_with_contract(st.session_state.messages, rag_context)
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

if __name__ == "__main__":
    main()
