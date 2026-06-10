from typing import Any
import chromadb
import ollama
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from cag_cache import fetch_cag_context
#----USE TRY CATCH and RAISE blocks in here since I had to make a POC ands test load values on a sysytem
# 1. Re-connect to local storage with local embedding engine bound safely
chroma_client = chromadb.PersistentClient(path="./chroma_db")
ollama_ef = OllamaEmbeddingFunction(url="http://localhost:11434", model_name="nomic-embed-text")

safe_ef: Any = ollama_ef
collection = chroma_client.get_collection(name="factory_schema", embedding_function=safe_ef)

def run_agent(user_input: str):
    #--------Must catch and posssibly raise an exception here (DML violation)-----#
    forbidden = ["drop", "delete", "update", "truncate", "alter"]
    if any(word in user_input.lower() for word in forbidden):
        return "Security Violation: Non-DML operations are restricted."

    # 2. Query the Collection safely -- init_rag.py 
    rag_results = collection.query(query_texts=[user_input], n_results=1)

    # 3. Defensively unpack vectors to completely satisfy the VS Code linter
    retrieved_schema = "No explicit schema matches found."
    if rag_results and "documents" in rag_results and rag_results["documents"]:
        document_list = rag_results["documents"]
        if document_list and len(document_list) > 0 and len(document_list[0]) > 0:
            retrieved_schema = document_list[0][0]

    # 4. CAG Layer Lookup --- cag_cache 
    cag_context = fetch_cag_context(user_input)

    # 5. Formulate System Directives --- the prompt 
    system_prompt = f"""
    You are a strict T-SQL engine translator for an automotive plant database.
    Convert user prompts into valid MSSQL 'INSERT INTO' queries based ONLY on the context below.
    
    RULES:
    - Never write SELECT, UPDATE, DELETE, or DROP operations.
    - Output ONLY valid SQL syntax inside a single code block. Do not provide code commentary or descriptions.
    - IDENTIFIER WRAPPING: You MUST wrap all database object names, schema names, table names, and column identifiers in square brackets `[]`. 
    - Example: Write `[dbo].[AssetMaster]` instead of `dbo.AssetMaster`.
    - Example: Write `([AssetID], [LineNumber])` instead of `(AssetID, LineNumber)`.

    TARGET SCHEMA CONTEXT (RAG):
    {retrieved_schema}

    ACTIVE ENUMERATED VALUES (CAG):
    {cag_context}
    """

    # 6. Fire up the 7B GPU Coder
    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response['message']['content']

if __name__ == "__main__":
    test_prompt = "Log a pressure reading of 42.5 bar for the stamping press on line 1."
    print(f"User Request: {test_prompt}\n" + "="*40)
    print(run_agent(test_prompt)) 

    # need to ewnsure saftety gaurdrails (forbidden) for the query post geneneration to reject and regenerate any DDL qury 
    # need to make sure to set a regenration in case of MSSQL error 
    # need to make sure to connect to DB instance for testing/Validation ? -
    # need to make sure to  test using docker for edge contrained Hardware 
    # need to make sure to add Try Except blocks 
    # need to make sure to expore other approaches, fox the Cache and Persistant logic - wher eto store what info 
    # need to take a prompt from the comand line 
    # need an actual Schema - maybe write to the RAG DB ?? - Need to pull the Schema itself from the DB and put it into the thing 
    # explore a more Optimal Prompt for the Agent     