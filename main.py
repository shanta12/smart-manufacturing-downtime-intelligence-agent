# main.py

from data.datasensor_logs       import generate_sensor_logs
from data.datasensor_logs       import generate_maintenance_history
from graph.graphneo4j_manager    import Neo4jManager
from agents.agentsworkflow       import ManufacturingAgent
from reports.reportsreport_generator import save_report


def main():
    print("=" * 60)
    print("  🏭 Smart Manufacturing Downtime Intelligence Agent")
    print("     Powered by Ollama LLaMA3 — 100% Free & Local")
    print("=" * 60)

    # ── 1. Generate Data ──
    print("\n📊 Step 1: Generating Factory Data...")
    sensor_logs         = generate_sensor_logs(num_machines=5, days=30)
    maintenance_history = generate_maintenance_history()

    # ── 2. Setup Neo4j ──
    print("\n🔗 Step 2: Setting Up Knowledge Graph...")
    neo4j = Neo4jManager()
    neo4j.clear_database()
    neo4j.create_machines()
    neo4j.create_production_lines()
    neo4j.create_relationships()

    # ── 3. Run AI Agent ──
    print("\n🤖 Step 3: Starting AI Agent Workflow...")
    agent    = ManufacturingAgent(neo4j_manager=neo4j)
    workflow = agent.build_workflow()

    initial_state = {
        "sensor_logs":         sensor_logs,
        "maintenance_history": maintenance_history,
        "anomalies":           [],
        "failing_machines":    [],
        "failure_probability": {},
        "impact_analysis":     {},
        "graph_context":       [],
        "root_cause_analysis": "",
        "maintenance_plan":    "",
        "executive_summary":   "",
        "current_step":        "start",
        "errors":              []
    }

    final_state = workflow.invoke(initial_state)

    # ── 4. Show Results ──
    print("\n" + "=" * 60)
    print("📋 EXECUTIVE SUMMARY")
    print("=" * 60)
    print(final_state["executive_summary"])

    print("\n" + "=" * 60)
    print("🔧 MAINTENANCE PLAN")
    print("=" * 60)
    print(final_state["maintenance_plan"])

    # ── 5. Save Report ──
    save_report(final_state)

    # ── 6. Close Neo4j ──
    neo4j.close()
    print("\n🎉 Project Complete! Check your report file.")


if __name__ == "__main__":
    main()