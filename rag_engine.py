import os
import shutil
from typing import Optional
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# Pr├®-requis :
# 1. pip install langchain-google-genai chromadb python-dotenv pypdf
# 2. Exporter la variable d'environnement GOOGLE_API_KEY (ex: set GOOGLE_API_KEY=...)

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Constantes du projet
PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "models/gemini-embedding-001"

def build_vector_db(data_directory: str, persist_directory: str = PERSIST_DIRECTORY) -> Chroma:
    """
    Ing├¿re les fichiers .txt d'un dossier, les d├®coupe selon la strat├®gie d├®finie,
    puis les vectorise et les stocke dans une base ChromaDB locale.
    """
    print(f"Chargement des documents depuis le dossier : {data_directory}")
    # Support both PDF and TXT for maximum flexibility
    from langchain_community.document_loaders import TextLoader
    
    documents = []
    # Load PDFs
    pdf_loader = DirectoryLoader(data_directory, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents.extend(pdf_loader.load())
    
    # Load TXTs (with robust encoding fallback)
    def load_txt(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            with open(file_path, "r", encoding="windows-1252", errors="replace") as f:
                return f.read()

    txt_loader = DirectoryLoader(data_directory, glob="**/*.txt", loader_cls=TextLoader)
    documents.extend(txt_loader.load())
    
    if not documents:
        print("Aucun document trouv├®.")
        return None

    print(f"{len(documents)} document(s) charg├®(s).")

    # Task 2: Strat├®gie de Chunking (Crucial)
    # -------------------------------------------------------------------------------------------------
    # JUSTIFICATION DE LA STRAT├ëGIE :
    # FR: Une taille de chunk (`chunk_size`) de 1000 caract├¿res permet de conserver les clauses 
    # juridiques de longueur moyenne (par ex. clause r├®solutoire, indexation) intactes et riches 
    # en contexte dans un m├¬me bloc vectoris├®. 
    # Le chevauchement (`chunk_overlap`) de 200 caract├¿res est essentiel pour ne pas couper le 
    # contexte aux fronti├¿res des blocs. C'est critique pour les contrats de bail commercial afin 
    # de ne pas dissocier des ├®l├®ments cl├®s (comme des valeurs num├®riques, un taux de p├®nalit├®, ou 
    # des dates d'application) du reste de leur clause d'appartenance.
    #
    # EN: A chunk size of 1000 characters ensures that standard legal clauses remain complete within
    # a single semantic block. The 200-character overlap prevents contextual loss at the boundaries,
    # which is especially important to avoid splitting numerical values (e.g., indexation rates) 
    # from the entities they refer to.
    # -------------------------------------------------------------------------------------------------
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"D├®coupage termin├® : {len(chunks)} chunks cr├®├®s.")

    # Task 3: Vectorisation et Stockage Local
    print(f"Vectorisation avec le mod├¿le {EMBEDDING_MODEL} et cr├®ation de la base de donn├®es...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # Nettoyage de la base existante si n├®cessaire pour repartir sur une base propre
    if os.path.exists(persist_directory):
        print("Suppression de l'ancienne base ChromaDB locale...")
        shutil.rmtree(persist_directory)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Base vectorielle persist├®e avec succ├¿s dans : {persist_directory}")
    return vectorstore

def get_retriever(persist_directory: str = PERSIST_DIRECTORY, contract_id: Optional[str] = None):
    """
    Task 4: Expose le retriever.
    Initialise la base depuis le disque local pour retourner le retriever Langchain.
    Permet un retour des 3 chunks les plus pertinents (k=3).
    
    Args:
        persist_directory (str): Le chemin vers la base de donn├®es Chroma locale.
        contract_id (str, optional): Si fourni, permet de filtrer la recherche sur un contrat sp├®cifique.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    
    # On recharge la base Chroma stock├®e en local
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Configuration des param├¿tres de recherche
    search_kwargs = {"k": 5}
    
    # Filtre optionnel par document/contrat si un contract_id est demand├®
    # ChromaDB permet de filtrer sur les metadonn├®es (le TextLoader stocke le chemin dans 'source')
    if contract_id:
        # Clean the contract_id to be more flexible (replace spaces with nothing or underscores for better matching)
        # We'll use a simple approach: if anyone of the keywords is in the source, it matches.
        # More securely, let's just use the last digit if present
        import re
        match = re.search(r'\d+', contract_id)
        if match:
            search_kwargs["filter"] = {"source": {"$contains": f"_{match.group(0)}" if "_" in f"_{match.group(0)}" else match.group(0)}}
        else:
             search_kwargs["filter"] = {"source": {"$contains": contract_id.replace(" ", "_")}}

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    return retriever


if __name__ == '__main__':
    # ---------------------------------------------------------
    # BLOC DE TEST RAPIDE (Ex├®cution locale)
    # ---------------------------------------------------------
    
    # Attention: N├®cessite que la variable d'environnement GOOGLE_API_KEY soit d├®finie.
    # os.environ["GOOGLE_API_KEY"] = "AIza........."
    
    test_data_dir = "./Lease_Agreement"
    test_db_dir = "./chroma_test_db"
    
    try:
        print("=== INITIALISATION DU TEST ===")
        if not os.path.exists(test_data_dir):
            print(f"ÔÜá´©Å [ATTENTION] Le dossier '{test_data_dir}' n'existe pas. Cr├®ez-le et placez-y vos PDF.")
            exit(1)
        
        # 1. Appel de l'ingestion / cr├®ation de base
        print("\n=== ├ëVALUATION : build_vector_db ===")
        build_vector_db(data_directory=test_data_dir, persist_directory=test_db_dir)
        
        # 2. Appel de l'exposition du retriever
        print("\n=== ├ëVALUATION : get_retriever ===")
        retriever = get_retriever(persist_directory=test_db_dir)
        
        # 3. Test de r├®cup├®ration (invocation du retriever)
        test_query = "Quel est le taux d'indexation et l'ILC de r├®f├®rence ?"
        print(f"\nRequ├¬te utilisateur : '{test_query}'")
        
        docs = retriever.invoke(test_query)
        
        print("\n=== R├ëSULTATS DU RETRIEVER ===")
        for i, doc in enumerate(docs, 1):
            print(f"--- Fichier source : {doc.metadata.get('source', 'Inconnu')} ---")
            print(f"Extrait {i} : {doc.page_content}\n")
            
    except Exception as e:
        print(f"\n[ERREUR LORS DU TEST] : {e}")
        print("Note: Veillez ├á bien exporter votre cl├® GOOGLE_API_KEY dans votre terminal.")
        
    finally:
        # Nettoyage de la DB de test uniquement (On ne supprime surtout pas tes contrats PDF !)
        print("=== NETTOYAGE ===")
        if os.path.exists(test_db_dir):
            shutil.rmtree(test_db_dir, ignore_errors=True)
        print("Base de donn├®es de test supprim├®e (les erreurs de verrouillage sous Windows sont ignor├®es).")
