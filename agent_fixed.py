# agent.py
from typing import Any
import chromadb
import ollama
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from cag_cache_new import fetch_cag_context

# Global Initializations (Executes once on script startup)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
ollama_ef = OllamaEmbeddingFunction(url="http://localhost:11434", model_name="nomic-embed-text")
safe_ef: Any = ollama_ef
collection = chroma_client.get_collection(name="factory_schema", embedding_function=safe_ef)
#collection = chroma_client.get_collection(name="factory_schema", embedding_function=ollama_ef)

def run_agent(user_input: str):
    # Security Guardrail (DML violation check)
    forbidden = ["drop", "delete", "update", "truncate", "alter" ]
    if any(word in user_input.lower() for word in forbidden):
        return "Security Violation: Non-DML operations are restricted."

    # ==========================================
    # STRATEGY CHANGE: 1. CHECK CAG CACHE FIRST
    # ==========================================
    cag_result = fetch_cag_context(user_input)
    cag_context = cag_result["context_string"]

    if cag_result["hit"]:
        # FAST PATH: Bypass Chroma entirely and use structural metadata from RAM
        retrieved_schema = cag_result["schema_fallback"]
        print(" [CAG HIT]: Bypassing RAG Vector Query. Using cached schema structure.")
    else:
        # SLOW PATH: Fallback to Chroma vector search only for novel/unknown inputs
        print(" [CAG MISS]: Querying RAG Vector Database...")
        rag_results = collection.query(query_texts=[user_input], n_results=1)
        
        retrieved_schema = "No explicit schema matches found."
        if rag_results and "documents" in rag_results and rag_results["documents"]:
            document_list = rag_results["documents"]
            if document_list and len(document_list) > 0 and len(document_list[0]) > 0:
                retrieved_schema = document_list[0][0]

    # 3. Formulate System Directives
    system_prompt = f"""
    You are a strict T-SQL engine translator for an automotive plant database.
    Convert user prompts into valid MSSQL queries based ONLY on the context below.
    
    RULES:
    - Never write  UPDATE, DELETE, or DROP operations.
    - Output ONLY valid SQL syntax inside a single code block. Do not provide code commentary or descriptions.
    - IDENTIFIER WRAPPING: You MUST wrap all database object names, schema names, table names, and column identifiers in square brackets `[]`. 
    - Example: Write `[dbo].[AssetMaster]` instead of `dbo.AssetMaster`.
    - Example: Write `([AssetID], [LineNumber])` instead of `(AssetID, LineNumber)`.

    TARGET SCHEMA CONTEXT:
    {retrieved_schema}

    ACTIVE ENUMERATED VALUES:
    {cag_context}
    """

    # 4. Fire up the Coder Model (Added keep_alive to keep it pinned in RAM)
    # Note: Swap "qwen2.5-coder:7b" to "qwen2.5-coder:1.5b" when deploying on non-GPU edge
    response = ollama.chat(
        model="qwen2.5-coder:1.5b ", #<----changed to 1.5 billion Parameter for insertion only
        #keep_alive="-1",  <------ to keep the LLM loaded into RAM permanenetly
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response['message']['content']

if __name__ == "__main__":
    test_prompt = "look for a pressure reading of 42.5 bar for the stamping press on line 1."
    print(f"User Request: {test_prompt}\n" + "="*40)
    print(run_agent(test_prompt))