# config.py

class Config:
    # ── Ollama Local LLM Settings ──
    # No API key needed!
    OLLAMA_BASE_URL = "http://localhost:11434"
    LLM_MODEL       = "llama3"

    # ── Neo4j Settings ──
    # Must match your Neo4j instance password
    NEO4J_URI      = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "password123"  # ← Change to your password

    # ── Manufacturing Alert Thresholds ──
    FAILURE_THRESHOLD            = 0.75  # 75% = Critical Alert
    CRITICAL_TEMP_THRESHOLD      = 85.0  # Celsius
    CRITICAL_VIBRATION_THRESHOLD = 8.5   # mm/s