# cag_cache.py
from typing import Any
# Expand the cache to explicitly map aliases to their strict SQL targets
PLANT_CACHE = {
    "stamping press on line 1": {
        "AssetID": 4021, 
        "TargetTable": "[dbo].[StampingPressLogs]",
        "SchemaHint": "Columns: [LogID] INT IDENTITY, [AssetID] INT, [Pressure_Bar] DECIMAL(5,2), [Timestamp] DATETIME"
    },
    "kuka welding robot on line 2": {
        "AssetID": 1042, 
        "TargetTable": "[dbo].[RoboticsTelemetry]",
        "SchemaHint": "Columns: [LogID] INT IDENTITY, [AssetID] INT, [Error_Code] INT, [Cycle_Time_Sec] FLOAT"
    },
    "conveyor belt line 3": {
        "AssetID": 8819, 
        "TargetTable": "[dbo].[ConveyorMetrics]",
        "SchemaHint": "Columns: [LogID] INT IDENTITY, [AssetID] INT, [Belt_Speed] DECIMAL(4,1)"
    }
}


METRIC_SYNONYMS = {
    "temp": "Temperature",
    "temperature": "Temperature",

    "pressure": "Pressure",
    "hydraulic pressure": "HydraulicPressure",

    "speed": "BeltSpeed",
    "belt speed": "BeltSpeed",

    "cycle time": "CycleTime",
    "cycletime": "CycleTime"
}

def fetch_cag_context(user_query: str) -> dict[str, Any]:
    """
    Returns a dictionary indicating if a hit occurred, along with structured metadata.
    """
    query_lower = user_query.lower()
    
    for key, data in PLANT_CACHE.items():
        if key in query_lower:
            return {
                "hit": True,
                "context_string": f"Literal context match: '{key}' maps strictly to [AssetID]: {data['AssetID']} in table {data['TargetTable']}.",
                "schema_fallback": data["SchemaHint"]
            }
            
    return {"hit": False, "context_string": "No explicit active asset indices detected.", "schema_fallback": None}