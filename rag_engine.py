import os
import shutil
from typing import Optional
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# Pré-requis :
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
    Ingère les fichiers .txt d'un dossier, les découpe selon la stratégie définie,
    puis les vectorise et les stocke dans une base ChromaDB locale.
    """
    print(f"Chargement des documents depuis le dossier : {data_directory}")
    # Task 1: Ingestion avec PyPDFLoader pour gérer les fichiers .pdf
    loader = DirectoryLoader(data_directory, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    
    if not documents:
        print("Aucun document trouvé.")
        return None

    print(f"{len(documents)} document(s) chargé(s).")

    # Task 2: Stratégie de Chunking (Crucial)
    # -------------------------------------------------------------------------------------------------
    # JUSTIFICATION DE LA STRATÉGIE :
    # FR: Une taille de chunk (`chunk_size`) de 1000 caractères permet de conserver les clauses 
    # juridiques de longueur moyenne (par ex. clause résolutoire, indexation) intactes et riches 
    # en contexte dans un même bloc vectorisé. 
    # Le chevauchement (`chunk_overlap`) de 200 caractères est essentiel pour ne pas couper le 
    # contexte aux frontières des blocs. C'est critique pour les contrats de bail commercial afin 
    # de ne pas dissocier des éléments clés (comme des valeurs numériques, un taux de pénalité, ou 
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
    print(f"Découpage terminé : {len(chunks)} chunks créés.")

    # Task 3: Vectorisation et Stockage Local
    print(f"Vectorisation avec le modèle {EMBEDDING_MODEL} et création de la base de données...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # Nettoyage de la base existante si nécessaire pour repartir sur une base propre
    if os.path.exists(persist_directory):
        print("Suppression de l'ancienne base ChromaDB locale...")
        shutil.rmtree(persist_directory)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Base vectorielle persistée avec succès dans : {persist_directory}")
    return vectorstore

def get_retriever(persist_directory: str = PERSIST_DIRECTORY, contract_id: Optional[str] = None):
    """
    Task 4: Expose le retriever.
    Initialise la base depuis le disque local pour retourner le retriever Langchain.
    Permet un retour des 3 chunks les plus pertinents (k=3).
    
    Args:
        persist_directory (str): Le chemin vers la base de données Chroma locale.
        contract_id (str, optional): Si fourni, permet de filtrer la recherche sur un contrat spécifique.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    
    # On recharge la base Chroma stockée en local
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Configuration des paramètres de recherche
    search_kwargs = {"k": 3}
    
    # Filtre optionnel par document/contrat si un contract_id est demandé
    # ChromaDB permet de filtrer sur les metadonnées (le TextLoader stocke le chemin dans 'source')
    if contract_id:
        # On suppose que l'ID est dans le nom du fichier
        search_kwargs["filter"] = {"source": {"$contains": contract_id}}

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    return retriever


if __name__ == '__main__':
    # ---------------------------------------------------------
    # BLOC DE TEST RAPIDE (Exécution locale)
    # ---------------------------------------------------------
    
    # Attention: Nécessite que la variable d'environnement GOOGLE_API_KEY soit définie.
    # os.environ["GOOGLE_API_KEY"] = "AIza........."
    
    test_data_dir = "./Lease_Agreement"
    test_db_dir = "./chroma_test_db"
    
    try:
        print("=== INITIALISATION DU TEST ===")
        if not os.path.exists(test_data_dir):
            print(f"⚠️ [ATTENTION] Le dossier '{test_data_dir}' n'existe pas. Créez-le et placez-y vos PDF.")
            exit(1)
        
        # 1. Appel de l'ingestion / création de base
        print("\n=== ÉVALUATION : build_vector_db ===")
        build_vector_db(data_directory=test_data_dir, persist_directory=test_db_dir)
        
        # 2. Appel de l'exposition du retriever
        print("\n=== ÉVALUATION : get_retriever ===")
        retriever = get_retriever(persist_directory=test_db_dir)
        
        # 3. Test de récupération (invocation du retriever)
        test_query = "Quel est le taux d'indexation et l'ILC de référence ?"
        print(f"\nRequête utilisateur : '{test_query}'")
        
        docs = retriever.invoke(test_query)
        
        print("\n=== RÉSULTATS DU RETRIEVER ===")
        for i, doc in enumerate(docs, 1):
            print(f"--- Fichier source : {doc.metadata.get('source', 'Inconnu')} ---")
            print(f"Extrait {i} : {doc.page_content}\n")
            
    except Exception as e:
        print(f"\n[ERREUR LORS DU TEST] : {e}")
        print("Note: Veillez à bien exporter votre clé GOOGLE_API_KEY dans votre terminal.")
        
    finally:
        # Nettoyage de la DB de test uniquement (On ne supprime surtout pas tes contrats PDF !)
        print("=== NETTOYAGE ===")
        if os.path.exists(test_db_dir):
            shutil.rmtree(test_db_dir, ignore_errors=True)
        print("Base de données de test supprimée (les erreurs de verrouillage sous Windows sont ignorées).")
