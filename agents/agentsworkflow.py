# agents/agentsworkflow.py

import json
import pandas as pd
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from config import Config


class ManufacturingState(TypedDict):
    sensor_logs:          Any
    maintenance_history:  Any
    anomalies:            List[Dict]
    failing_machines:     List[str]
    failure_probability:  Dict[str, float]
    impact_analysis:      Dict[str, Any]
    graph_context:        List[Dict]
    root_cause_analysis:  str
    maintenance_plan:     str
    executive_summary:    str
    current_step:         str
    errors:               List[str]


class ManufacturingAgent:

    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.llm = ChatOllama(
            model=Config.LLM_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.3
        )
        print("✅ Ollama LLM Ready — No API Key Needed!")

    def ingest_sensor_logs(self, state: ManufacturingState) -> ManufacturingState:
        print("\n🔍 Step 1: Analyzing Sensor Logs...")
        df = state["sensor_logs"]
        anomalies = []
        failure_probability = {}
        failing_machines = []

        for machine_id in df["machine_id"].unique():
            data = df[df["machine_id"] == machine_id].tail(24)
            avg_temp = data["temperature"].mean()
            avg_vibration = data["vibration"].mean()
            avg_pressure = data["pressure"].mean()
            error_count = (data["error_code"] != "NONE").sum()
            score = 0.0
            reasons = []

            if avg_temp > Config.CRITICAL_TEMP_THRESHOLD:
                score += 0.35
                reasons.append(f"High Temp: {avg_temp:.1f}C")

            if avg_vibration > Config.CRITICAL_VIBRATION_THRESHOLD:
                score += 0.35
                reasons.append(f"High Vibration: {avg_vibration:.1f}")

            if error_count > 3:
                score += 0.20
                reasons.append(f"Errors: {error_count} in 24hrs")

            if avg_pressure < 85:
                score += 0.10
                reasons.append(f"Low Pressure: {avg_pressure:.1f}")

            score = round(score, 2)
            failure_probability[machine_id] = score

            if score >= Config.FAILURE_THRESHOLD:
                failing_machines.append(machine_id)
                anomalies.append({
                    "machine_id": machine_id,
                    "failure_probability": score,
                    "avg_temperature": round(avg_temp, 2),
                    "avg_vibration": round(avg_vibration, 2),
                    "avg_pressure": round(avg_pressure, 2),
                    "error_count": int(error_count),
                    "reasons": reasons
                })
                print(f"   ⚠️  {machine_id} → Risk: {score*100:.0f}%")
            else:
                print(f"   ✅ {machine_id} → Normal ({score*100:.0f}%)")

        state["anomalies"] = anomalies
        state["failing_machines"] = failing_machines
        state["failure_probability"] = failure_probability
        state["current_step"] = "sensor_done"
        return state

    def analyze_graph_impact(self, state: ManufacturingState) -> ManufacturingState:
        print("\n🔗 Step 2: Querying Neo4j Graph...")
        impact_analysis = {}

        for machine_id in state["failing_machines"]:
            impact = self.neo4j.get_failure_impact(machine_id)
            impact_analysis[machine_id] = impact
            print(f"   📊 {machine_id} affects "
                  f"{len(impact['affected_machines'])} machines "
                  f"and {len(impact['impacted_lines'])} lines")

        state["impact_analysis"] = impact_analysis
        state["graph_context"] = self.neo4j.get_full_graph_summary()
        state["current_step"] = "graph_done"
        return state

    def identify_root_cause(self, state: ManufacturingState) -> ManufacturingState:
        print("\n🧠 Step 3: AI Root Cause Analysis...")
        print("   ⏳ Please wait — Local LLM is thinking...")

        maintenance_str = state["maintenance_history"][
            state["maintenance_history"]["machine_id"].isin(
                state["failing_machines"]
            )
        ].to_string()

        graph_str = "\n".join([
            f"{r['from_name']} --[{r['relationship']}]--> {r['to_name']}"
            for r in state["graph_context"]
        ])

        prompt = f"""
        You are a manufacturing engineer.

        ANOMALIES DETECTED:
        {json.dumps(state["anomalies"], indent=2)}

        PAST MAINTENANCE HISTORY:
        {maintenance_str}

        MACHINE DEPENDENCY MAP:
        {graph_str}

        Please provide:
        1. Root cause for each failing machine
        2. Is this a recurring problem?
        3. Risk of other machines failing next
        4. Estimated time before complete failure
        """

        response = self.llm.invoke([
            SystemMessage(content="You are a predictive maintenance expert."),
            HumanMessage(content=prompt)
        ])

        state["root_cause_analysis"] = response.content
        state["current_step"] = "rootcause_done"
        print("   ✅ Root cause identified")
        return state

    def generate_maintenance_plan(self, state: ManufacturingState) -> ManufacturingState:
        print("\n🔧 Step 4: Creating Maintenance Plan...")
        print("   ⏳ Please wait — Local LLM is thinking...")

        prompt = f"""
        Based on this analysis create a maintenance plan.

        ROOT CAUSE FOUND:
        {state["root_cause_analysis"]}

        FACTORY IMPACT:
        {json.dumps(state["impact_analysis"], indent=2)}

        Create a plan with these sections:
        1. IMMEDIATE ACTIONS  — What to do in next 24 hours
        2. SHORT TERM ACTIONS — What to do in next 7 days
        3. PREVENTION PLAN    — What to do in next 30 days
        4. COST ESTIMATE      — Expected repair costs
        """

        response = self.llm.invoke([
            SystemMessage(content="You are a maintenance planning expert."),
            HumanMessage(content=prompt)
        ])

        state["maintenance_plan"] = response.content
        state["current_step"] = "plan_done"
        print("   ✅ Maintenance plan created")
        return state

    def generate_executive_summary(self, state: ManufacturingState) -> ManufacturingState:
        print("\n📋 Step 5: Writing Executive Summary...")
        print("   ⏳ Please wait — Local LLM is thinking...")

        impacted_lines = set()
        for impact in state["impact_analysis"].values():
            for line in impact["impacted_lines"]:
                impacted_lines.add(line["line_name"])

        prompt = f"""
        Write a simple 1 page summary for the Plant Manager.

        SITUATION:
        - {len(state["failing_machines"])} machine(s) about to fail
        - Production lines at risk: {", ".join(impacted_lines)}
        - Failing machines: {", ".join(state["failing_machines"])}

        ROOT CAUSE SUMMARY:
        {state["root_cause_analysis"][:400]}

        MAINTENANCE PLAN SUMMARY:
        {state["maintenance_plan"][:400]}

        Write using these sections:
        1. What is happening right now
        2. Business impact if ignored
        3. Top 3 actions needed immediately
        4. Expected outcome if actions taken
        5. Management approval needed

        Use simple language. No technical jargon.
        Use emojis to make it easy to read.
        """

        response = self.llm.invoke([
            SystemMessage(content="You write reports for plant managers."),
            HumanMessage(content=prompt)
        ])

        state["executive_summary"] = response.content
        state["current_step"] = "complete"
        print("   ✅ Executive summary ready")
        return state

    def build_workflow(self):
        print("\n⚙️  Building LangGraph Workflow...")

        workflow = StateGraph(ManufacturingState)

        workflow.add_node("ingest_logs",      self.ingest_sensor_logs)
        workflow.add_node("graph_impact",     self.analyze_graph_impact)
        workflow.add_node("root_cause",       self.identify_root_cause)
        workflow.add_node("maintenance_plan", self.generate_maintenance_plan)
        workflow.add_node("exec_summary",     self.generate_executive_summary)

        workflow.set_entry_point("ingest_logs")
        workflow.add_edge("ingest_logs",      "graph_impact")
        workflow.add_edge("graph_impact",     "root_cause")
        workflow.add_edge("root_cause",       "maintenance_plan")
        workflow.add_edge("maintenance_plan", "exec_summary")
        workflow.add_edge("exec_summary",     END)

        print("✅ Workflow built successfully")
        return workflow.compile()