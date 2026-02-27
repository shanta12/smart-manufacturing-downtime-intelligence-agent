# test_neo4j.py

from neo4j import GraphDatabase

URI      = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password123"  # ← Your Neo4j password

try:
    driver  = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    session = driver.session()
    result  = session.run("RETURN 'Neo4j Connected!' AS message")
    record  = result.single()
    print("✅", record["message"])
    print("✅ Neo4j is ready — proceed to main.py")
    session.close()
    driver.close()

except Exception as e:
    print("❌ Connection Failed:", e)
    print("👉 Check Neo4j Desktop is running (green dot)")