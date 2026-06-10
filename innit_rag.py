from typing import Any
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
# Creates a persistent vector index on your hard drive
chroma_client = chromadb.PersistentClient(path="./chroma_db")
#collection = chroma_client.get_or_create_collection(name="factory_schema")


ollama_ef = OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="nomic-embed-text"
)

safe_ef : Any  = ollama_ef
collection = chroma_client.get_or_create_collection(
    name="factory_schema",
    embedding_function=safe_ef 
)
 
tables_ddl = [
    """
    Table: dbo.AssetMaster
    Columns:
        - AssetID (INT, PRIMARY KEY)
        - LineNumber (VARCHAR(50)) - e.g., 'Line 1', 'Line 2'
        - AssetType (VARCHAR(50)) - e.g., 'Robot', 'Conveyor', 'Press'
    Description: Registry tracking heavy physical assets located on the assembly floor.
    """,
    """
    Table: dbo.TelemetryLogs
    Columns:
        - LogID (BIGINT, PRIMARY KEY IDENTITY)
        - AssetID (INT, FOREIGN KEY referencing dbo.AssetMaster)
        - Timestamp (DATETIME2)
        - MetricName (VARCHAR(100)) - e.g., 'Temperature', 'HydraulicPressure'
        - Value (FLOAT)
    Description: Relational DML landing table capturing IIoT log streams from the factory.
    """
]

collection.add(
    documents=tables_ddl,
    ids=["asset_master_ddl", "telemetry_logs_ddl"],
    metadatas=[{"type": "schema"}, {"type": "schema"}]
)
print("ChromaDB vector initialization complete.")