import os
import shutil
import re
from typing import Optional, List
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Constantes du projet
PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "models/gemini-embedding-001"

def build_vector_db(persist_directory: str = PERSIST_DIRECTORY) -> Chroma:
    """
    Ingère les documents depuis plusieurs sources (Contrats, Lois AL, Lois NY),
    injecte les métadonnées de filtrage, les découpe, et les stocke dans ChromaDB.
    """
    all_documents = []
    
    # Définition des sources et de leurs métadonnées associées
    # Chaque source est un tuple (chemin, doc_type, state)
    sources = [
        ("./data/contracts", "contract", None),
        ("./data/laws/AL", "law", "AL"),
        ("./data/laws/NY", "law", "NY"),
    ]
    
    print("=== Démarrage de l'ingestion multi-sources ===")
    
    for path, doc_type, state in sources:
        if not os.path.exists(path):
            print(f"⚠ [INFOS] Le dossier '{path}' n'existe pas. Passage à la source suivante.")
            continue
            
        print(f"Chargement de : {path} (type={doc_type}, state={state})")
        
        # Chargement des PDFs
        pdf_loader = DirectoryLoader(path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        source_docs = pdf_loader.load()
        
        # Chargement des TXTs
        txt_loader = DirectoryLoader(path, glob="**/*.txt", loader_cls=TextLoader)
        source_docs.extend(txt_loader.load())
        
        # Injection des métadonnées personnalisées pour le filtrage
        for doc in source_docs:
            doc.metadata["doc_type"] = doc_type
            if state:
                doc.metadata["state"] = state
        
        all_documents.extend(source_docs)

    if not all_documents:
        print("❌ Aucun document trouvé dans les sources spécifiées.")
        return None

    print(f"Total documents chargés : {len(all_documents)}")

    # Stratégie de Chunking (1000/200) - Conservée selon spécifications
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(all_documents)
    print(f"Découpage terminé : {len(chunks)} chunks créés avec métadonnées injectées.")

    # Vectorisation et Stockage Local
    print(f"Vectorisation avec {EMBEDDING_MODEL}...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    if os.path.exists(persist_directory):
        print("Nettoyage de l'ancienne base ChromaDB...")
        shutil.rmtree(persist_directory, ignore_errors=True)

    # Initialisation de la base vectorielle avec un PersistentClient (Fix: no such table: tenants)
    batch_size = 50
    print(f"Indexation par lots de {batch_size} pour respecter les quotas API...")
    
    import chromadb
    client = chromadb.PersistentClient(path=persist_directory)
    
    # On utilise langchain_chroma ou langchain_community selon les dépendances
    try:
        from langchain_chroma import Chroma as LangchainChroma
        vectorstore = LangchainChroma(
            client=client,
            embedding_function=embeddings,
        )
    except ImportError:
        vectorstore = Chroma(
            client=client,
            embedding_function=embeddings,
        )

    import time
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"Lot {i//batch_size + 1}/{len(chunks)//batch_size + 1} indexé...")
        time.sleep(2)
    
    print(f"Base vectorielle persistée dans : {persist_directory}")
    return vectorstore

def get_retriever(persist_directory: str = PERSIST_DIRECTORY, 
                  doc_type: Optional[str] = None, 
                  state: Optional[str] = None,
                  k: int = 6):
    """
    Expose le retriever avec support de filtrage par métadonnées.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    
    import chromadb
    client = chromadb.PersistentClient(path=persist_directory)
    
    try:
        from langchain_chroma import Chroma as LangchainChroma
        vectorstore = LangchainChroma(
            client=client,
            embedding_function=embeddings,
        )
    except ImportError:
        vectorstore = Chroma(
            client=client,
            embedding_function=embeddings,
        )
    
    search_kwargs = {"k": k}
    
    # Construction dynamique du filtre ChromaDB
    # Utilise la syntaxe $and si plusieurs filtres sont actifs
    filters = []
    if doc_type:
        filters.append({"doc_type": {"$eq": doc_type}})
    if state:
        filters.append({"state": {"$eq": state}})
        
    if filters:
        if len(filters) == 1:
            search_kwargs["filter"] = filters[0]
        else:
            search_kwargs["filter"] = {"$and": filters}

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    return retriever

if __name__ == '__main__':
    # --- BLOC DE TEST DU PIVOT MULTI-SOURCES ---
    test_db_dir = "./chroma_pivot_test_db"
    
    try:
        print("\n[TEST] 1. Ingestion Multi-Sources")
        # Note: Si les dossiers sont vides ou absents, le code affichera un warning mais ne plantera pas.
        build_vector_db(persist_directory=test_db_dir)
        
        print("\n[TEST] 2. Test du Filtrage Métadonnées (Loi NY)")
        # Simulation d'une recherche uniquement dans les lois de New York
        retriever_ny = get_retriever(persist_directory=test_db_dir, doc_type="law", state="NY")
        
        test_query = "Quelles sont les obligations du bailleur concernant les réparations structurelles ?"
        print(f"Requête filtrée (Laws/NY) : '{test_query}'")
        
        # Le retriever renverra une liste vide s'il n'y a pas de documents NY dans la DB
        docs = retriever_ny.invoke(test_query)
        
        print(f"\n=== RESULTATS DU TEST ({len(docs)} documents trouvés) ===")
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Inconnu')
            d_type = doc.metadata.get('doc_type', 'N/A')
            st = doc.metadata.get('state', 'N/A')
            print(f"[{i}] Source: {source} | Type: {d_type} | State: {st}")
            # print(f"Contenu : {doc.page_content[:100]}...\n")
            
    except Exception as e:
        print(f"\n❌ [ERREUR TEST] : {e}")
        
    finally:
        if os.path.exists(test_db_dir):
            shutil.rmtree(test_db_dir, ignore_errors=True)
        print("\n[TEST] Nettoyage terminé.")
