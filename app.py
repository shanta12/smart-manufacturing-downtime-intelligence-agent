# app.py — Smart Manufacturing Downtime Intelligence
# Easy to understand dashboard for everyone

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.datasensor_logs              import generate_sensor_logs
from data.datasensor_logs              import generate_maintenance_history
from graph.graphneo4j_manager          import Neo4jManager
from agents.agentsworkflow             import ManufacturingAgent
from reports.reportsreport_generator   import save_report

# ─────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────
st.set_page_config(
    page_title = "🏭 Factory Health Monitor",
    page_icon  = "🏭",
    layout     = "wide"
)

# ─────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .main { background-color: #f0f2f6; }

    /* Machine card styles */
    .machine-card {
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .card-critical {
        background: linear-gradient(135deg, #ff4444, #cc0000);
        color: white;
        border: 3px solid #ff0000;
        animation: blink 1s infinite;
    }
    .card-warning {
        background: linear-gradient(135deg, #ffaa00, #cc8800);
        color: white;
        border: 3px solid #ffaa00;
    }
    .card-normal {
        background: linear-gradient(135deg, #00aa44, #007733);
        color: white;
        border: 3px solid #00aa44;
    }

    /* Section headers */
    .section-title {
        font-size: 24px;
        font-weight: bold;
        color: #1a1a2e;
        padding: 10px 0;
        border-bottom: 3px solid #4a90d9;
        margin-bottom: 20px;
    }

    /* Info boxes */
    .info-box {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4a90d9;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .info-box-red {
        border-left: 5px solid #ff4444;
        background: #fff5f5;
    }
    .info-box-green {
        border-left: 5px solid #00aa44;
        background: #f0fff4;
    }

    /* Big number display */
    .big-number {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
    }

    /* Status badge */
    .badge-critical {
        background: #ff4444;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .badge-normal {
        background: #00aa44;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }

    /* Hide streamlit menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# MACHINE DATA
# ─────────────────────────────────────────
MACHINES = {
    "M001": {
        "name":     "CNC Machine A",
        "type":     "Metal Cutting",
        "location": "Plant North",
        "vendor":   "Siemens",
        "emoji":    "⚙️"
    },
    "M002": {
        "name":     "Conveyor Belt B",
        "type":     "Parts Transport",
        "location": "Plant North",
        "vendor":   "ABB",
        "emoji":    "🔄"
    },
    "M003": {
        "name":     "Robotic Arm C",
        "type":     "Assembly Robot",
        "location": "Plant South",
        "vendor":   "FANUC",
        "emoji":    "🦾"
    },
    "M004": {
        "name":     "Hydraulic Press D",
        "type":     "Metal Forming",
        "location": "Plant South",
        "vendor":   "Bosch",
        "emoji":    "🔩"
    },
    "M005": {
        "name":     "Assembly Unit E",
        "type":     "Final Assembly",
        "location": "Plant North",
        "vendor":   "Siemens",
        "emoji":    "🏗️"
    },
}


# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────
def get_status(risk):
    if risk >= 0.75:
        return "🔴 CRITICAL", "card-critical", "#ff4444"
    elif risk >= 0.40:
        return "🟡 WARNING",  "card-warning",  "#ffaa00"
    else:
        return "🟢 HEALTHY",  "card-normal",   "#00aa44"


def render_machine_gauge(machine_id, risk_score):
    machine  = MACHINES.get(machine_id, {})
    name     = machine.get("name",  machine_id)
    emoji    = machine.get("emoji", "⚙️")
    location = machine.get("location", "")
    _, _, color = get_status(risk_score)

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = risk_score * 100,
        title = {
            "text": (
                f"<b>{emoji} {machine_id}</b><br>"
                f"<span style='font-size:12px'>{name}</span><br>"
                f"<span style='font-size:10px;color:gray'>{location}</span>"
            ),
            "font": {"size": 13, "color": "#1a1a2e"}
        },
        number = {
            "suffix":   "%",
            "font":     {"size": 26, "color": color},
            "valueformat": ".0f"
        },
        gauge = {
            "axis": {
                "range":    [0, 100],
                "tickwidth": 1,
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0%", "25%", "50%", "75%", "100%"],
                "tickfont": {"size": 9}
            },
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0,  40],  "color": "#d4edda"},
                {"range": [40, 75],  "color": "#fff3cd"},
                {"range": [75, 100], "color": "#f8d7da"},
            ],
            "threshold": {
                "line":      {"color": "red", "width": 4},
                "thickness": 0.75,
                "value":     75
            }
        }
    ))

    fig.update_layout(
        height        = 280,
        margin        = dict(l=15, r=15, t=100, b=15),
        paper_bgcolor = "white",
        font_color    = "#1a1a2e",
        plot_bgcolor  = "white"
    )
    return fig


def render_sensor_chart(sensor_logs, machine_id):
    machine      = MACHINES.get(machine_id, {})
    machine_name = machine.get("name", machine_id)
    data         = sensor_logs[
        sensor_logs["machine_id"] == machine_id
    ].tail(72)

    fig = go.Figure()

    # Temperature line
    fig.add_trace(go.Scatter(
        x    = data["timestamp"],
        y    = data["temperature"],
        name = "🌡️ Temperature (°C)",
        line = dict(color="#ff4444", width=2),
        fill = "tozeroy",
        fillcolor = "rgba(255,68,68,0.1)"
    ))

    # Vibration line
    fig.add_trace(go.Scatter(
        x    = data["timestamp"],
        y    = data["vibration"],
        name = "📳 Vibration (mm/s)",
        line = dict(color="#ffaa00", width=2),
        yaxis = "y2"
    ))

    # Danger limit line
    fig.add_hline(
        y               = 85,
        line_dash       = "dash",
        line_color      = "red",
        line_width      = 2,
        annotation_text = "⚠️ Temperature Danger Limit (85°C)",
        annotation_font_color = "red"
    )

    fig.update_layout(
        title = {
            "text": f"📈 Sensor Readings — {machine_name} (Last 3 Days)",
            "font": {"size": 16, "color": "#1a1a2e"}
        },
        paper_bgcolor = "white",
        plot_bgcolor  = "#f8f9fa",
        font_color    = "#1a1a2e",
        height        = 320,
        xaxis = dict(
            title     = "Date and Time",
            showgrid  = True,
            gridcolor = "#e0e0e0"
        ),
        yaxis = dict(
            title     = "Temperature (°C)",
            color     = "#ff4444",
            showgrid  = True,
            gridcolor = "#e0e0e0"
        ),
        yaxis2 = dict(
            title      = "Vibration (mm/s)",
            color      = "#ffaa00",
            overlaying = "y",
            side       = "right"
        ),
        legend = dict(
            bgcolor      = "white",
            bordercolor  = "#e0e0e0",
            borderwidth  = 1,
            orientation  = "h",
            yanchor      = "bottom",
            y            = 1.02,
            xanchor      = "right",
            x            = 1
        )
    )
    return fig


def render_dependency_chart(graph_context):
    positions = {
        "CNC Machine A":       (1, 2),
        "Conveyor Belt B":     (2, 1),
        "Robotic Arm C":       (4, 2),
        "Hydraulic Press D":   (4, 1),
        "Assembly Unit E":     (2, 3),
        "Engine Assembly Line":(1, 4),
        "Body Welding Line":   (4, 4),
        "Paint Shop Line":     (2.5, 5),
    }

    colors = {
        "CNC Machine A":       "#4a90d9",
        "Conveyor Belt B":     "#ff4444",
        "Robotic Arm C":       "#4a90d9",
        "Hydraulic Press D":   "#4a90d9",
        "Assembly Unit E":     "#ff8800",
        "Engine Assembly Line":"#9b59b6",
        "Body Welding Line":   "#9b59b6",
        "Paint Shop Line":     "#9b59b6",
    }

    edges_x = []
    edges_y = []

    for rel in graph_context:
        from_name = rel.get("from_name", "")
        to_name   = rel.get("to_name",   "")
        if from_name in positions and to_name in positions:
            edges_x += [
                positions[from_name][0],
                positions[to_name][0],
                None
            ]
            edges_y += [
                positions[from_name][1],
                positions[to_name][1],
                None
            ]

    fig = go.Figure()

    # Draw edges
    fig.add_trace(go.Scatter(
        x         = edges_x,
        y         = edges_y,
        mode      = "lines",
        line      = dict(color="#cccccc", width=2),
        hoverinfo = "none",
        showlegend = False
    ))

    # Draw nodes
    for name, pos in positions.items():
        color = colors.get(name, "#4a90d9")
        size  = 30 if "Line" in name else 25

        fig.add_trace(go.Scatter(
            x          = [pos[0]],
            y          = [pos[1]],
            mode       = "markers+text",
            text       = [name],
            textposition = "top center",
            textfont   = {"size": 10, "color": "#1a1a2e"},
            marker     = dict(
                size  = size,
                color = color,
                line  = dict(color="white", width=2),
                symbol = "circle"
            ),
            hovertext  = name,
            hoverinfo  = "text",
            showlegend = False
        ))

    fig.update_layout(
        title = {
            "text": "🔗 How Machines Are Connected",
            "font": {"size": 16, "color": "#1a1a2e"}
        },
        paper_bgcolor = "white",
        plot_bgcolor  = "#f8f9fa",
        height        = 400,
        xaxis = dict(
            showgrid       = False,
            zeroline       = False,
            showticklabels = False,
            range          = [0, 5.5]
        ),
        yaxis = dict(
            showgrid       = False,
            zeroline       = False,
            showticklabels = False,
            range          = [0, 6]
        )
    )

    # Add legend boxes
    fig.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper",
        text="🔴 Failing Machine<br>🔵 Healthy Machine<br>🟣 Production Line<br>🟠 High Risk Machine",
        showarrow=False,
        font=dict(size=10),
        align="left",
        bgcolor="white",
        bordercolor="#cccccc",
        borderwidth=1
    )

    return fig


# ─────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────
def main():

    # ── HEADER ──
    st.markdown("""
    <div style='text-align:center; padding:20px 0;
                background:linear-gradient(135deg,#1a1a2e,#16213e);
                border-radius:15px; margin-bottom:20px;'>
        <h1 style='color:#00d4ff; margin:0; font-size:36px;'>
            🏭 Factory Health Monitor
        </h1>
        <p style='color:#8899aa; margin:5px 0 0 0; font-size:16px;'>
            AI powered early warning system for machine failures
        </p>
        <p style='color:#556677; margin:5px 0 0 0; font-size:13px;'>
            Powered by LangGraph + Neo4j + Ollama LLaMA3 — 100% Free & Local
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("## ⚙️ Control Panel")
        st.markdown("---")

        st.markdown("### 📅 How Much Data to Analyze")
        num_days = st.slider(
            "Number of days",
            min_value = 7,
            max_value = 60,
            value     = 30,
            help      = "More days = more accurate analysis"
        )
        st.caption(f"Analyzing last {num_days} days of sensor data")

        st.markdown("---")
        st.markdown("### 🚨 Alert Sensitivity")
        threshold = st.slider(
            "Alert when risk reaches (%)",
            min_value = 50,
            max_value = 95,
            value     = 75,
            help      = "Lower = more sensitive alerts"
        )
        st.caption(f"Alert fires when risk exceeds {threshold}%")

        st.markdown("---")
        st.markdown("### 🔌 Database Connection")
        neo4j_password = st.text_input(
            "Neo4j Password",
            value = "password123",
            type  = "password",
            help  = "Password you set when creating Neo4j database"
        )

        st.markdown("---")

        # Big run button
        run_button = st.button(
            "🚀 START ANALYSIS",
            use_container_width = True,
            type = "primary"
        )

        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.info("🤖 AI: Ollama LLaMA3\n\n🗄️ DB: Neo4j Graph\n\n🔄 Agent: LangGraph")

    # ── WELCOME SCREEN ──
    if not run_button:
        st.markdown("## 👋 Welcome to Factory Health Monitor")
        st.markdown(
            "This system watches your factory machines and "
            "warns you **before** they break down."
        )

        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class='info-box'>
                <h3>🔍 Step 1</h3>
                <b>Read Sensor Data</b>
                <p>Reads temperature, vibration
                and pressure from all machines
                every hour</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='info-box'>
                <h3>🔗 Step 2</h3>
                <b>Check Dependencies</b>
                <p>Finds which other machines
                will stop if one machine
                breaks down</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class='info-box'>
                <h3>🧠 Step 3</h3>
                <b>AI Analysis</b>
                <p>AI finds the root cause
                and predicts how long before
                complete failure</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class='info-box'>
                <h3>📋 Step 4</h3>
                <b>Action Plan</b>
                <p>Creates a maintenance plan
                with costs and timeline
                for your team</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 🏭 Machines Being Monitored")
        cols = st.columns(5)
        for i, (mid, info) in enumerate(MACHINES.items()):
            with cols[i]:
                st.markdown(f"""
                <div style='background:white; padding:15px;
                            border-radius:10px; text-align:center;
                            box-shadow:0 2px 8px rgba(0,0,0,0.1);'>
                    <div style='font-size:32px'>{info['emoji']}</div>
                    <b style='color:#1a1a2e'>{mid}</b><br>
                    <span style='color:#4a90d9; font-size:13px'>
                        {info['name']}
                    </span><br>
                    <span style='color:#888; font-size:11px'>
                        {info['type']}
                    </span><br>
                    <span style='color:#aaa; font-size:11px'>
                        📍 {info['location']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "### 👈 Click **START ANALYSIS** in the left panel to begin!"
        )
        return

    # ── RUN ANALYSIS ──
    st.markdown("## 🔄 Running Analysis...")
    progress = st.progress(0)
    status   = st.empty()

    # Connect Neo4j
    status.info("🔗 Connecting to database...")
    progress.progress(10)
    try:
        from config import Config
        Config.NEO4J_PASSWORD    = neo4j_password
        Config.FAILURE_THRESHOLD = threshold / 100

        neo4j = Neo4jManager()
        neo4j.clear_database()
        neo4j.create_machines()
        neo4j.create_production_lines()
        neo4j.create_relationships()
        st.sidebar.success("✅ Database Connected")
    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        st.warning("👉 Make sure Neo4j Desktop is open and database is started!")
        return

    # Generate data
    status.info("📊 Loading sensor data...")
    progress.progress(20)
    sensor_logs         = generate_sensor_logs(days=num_days)
    maintenance_history = generate_maintenance_history()
    st.sidebar.success("✅ Sensor Data Loaded")

    # Build agent
    status.info("🤖 Starting AI Agent...")
    progress.progress(30)
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

    # Run workflow
    status.warning(
        "🧠 AI is analyzing your machines... "
        "This takes 5-10 minutes. Please wait..."
    )
    progress.progress(40)

    with st.spinner(
        "⏳ AI Agent is thinking... Do not close this window!"
    ):
        final_state = workflow.invoke(initial_state)

    progress.progress(100)
    status.empty()

    # Save report
    save_report(final_state)
    neo4j.close()

    # ── SUCCESS MESSAGE ──
    st.balloons()
    st.success("🎉 Analysis Complete! Scroll down to see results.")
    st.markdown("---")

    # ── QUICK SUMMARY BAR ──
    failing  = final_state["failing_machines"]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label = "🏭 Machines Monitored",
            value = "5",
            delta = "All Active"
        )
    with col2:
        st.metric(
            label = "🔴 Critical Machines",
            value = str(len(failing)),
            delta = "Need Attention" if failing else "All Good",
            delta_color = "inverse" if failing else "normal"
        )
    with col3:
        total_impact = sum(
            len(v.get("affected_machines", []))
            for v in final_state["impact_analysis"].values()
        )
        st.metric(
            label = "⚠️ Affected Machines",
            value = str(total_impact),
            delta = "At Risk" if total_impact > 0 else "None"
        )
    with col4:
        total_lines = sum(
            len(v.get("impacted_lines", []))
            for v in final_state["impact_analysis"].values()
        )
        st.metric(
            label = "🏗️ Production Lines at Risk",
            value = str(total_lines),
            delta = "May Stop" if total_lines > 0 else "Safe"
        )

    st.markdown("---")

    # ── MACHINE RISK DASHBOARD ──
    st.markdown(
        "<div class='section-title'>📊 Machine Health Status</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "Each circle below shows the health of one machine. "
        "**Red = needs urgent attention. Green = healthy.**"
    )

    cols     = st.columns(5)
    machines = list(MACHINES.keys())

    for i, machine_id in enumerate(machines):
        with cols[i]:
            risk         = final_state["failure_probability"].get(
                machine_id, 0
            )
            machine_info = MACHINES[machine_id]
            status_text, _, color = get_status(risk)

            # Gauge chart
            fig = render_machine_gauge(machine_id, risk)
            st.plotly_chart(fig, use_container_width=True)

            # Info card below gauge
            st.markdown(f"""
            <div style='background:white; padding:12px;
                        border-radius:10px; text-align:center;
                        border-top: 4px solid {color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <div style='font-size:24px'>
                    {machine_info['emoji']}
                </div>
                <div style='font-weight:bold; color:#1a1a2e;
                            font-size:14px;'>
                    {machine_id}
                </div>
                <div style='color:#4a90d9; font-size:12px;
                            margin:3px 0;'>
                    {machine_info['name']}
                </div>
                <div style='color:#888; font-size:11px;'>
                    {machine_info['type']}
                </div>
                <div style='color:#aaa; font-size:10px;'>
                    📍 {machine_info['location']}
                </div>
                <div style='margin-top:8px; font-weight:bold;
                            color:{color}; font-size:16px;'>
                    {status_text}
                </div>
                <div style='color:{color}; font-size:20px;
                            font-weight:bold;'>
                    Risk: {risk*100:.0f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── CRITICAL ALERT BOX ──
    if failing:
        for machine_id in failing:
            machine_info = MACHINES.get(machine_id, {})
            impact       = final_state["impact_analysis"].get(
                machine_id, {}
            )
            affected     = impact.get("affected_machines", [])
            lines        = impact.get("impacted_lines",    [])

            st.markdown(f"""
            <div style='background:#fff0f0; border:2px solid #ff4444;
                        border-radius:15px; padding:20px; margin:10px 0;'>
                <h2 style='color:#ff4444; margin:0;'>
                    🚨 URGENT ALERT — {machine_info.get('emoji','⚙️')}
                    {machine_info.get('name', machine_id)} is About to Fail!
                </h2>
                <p style='color:#cc0000; font-size:16px; margin:10px 0;'>
                    Machine ID: <b>{machine_id}</b> |
                    Location: <b>{machine_info.get('location','')}</b> |
                    Vendor: <b>{machine_info.get('vendor','')}</b>
                </p>
                <hr style='border-color:#ffcccc;'>
                <p style='color:#660000; font-size:15px;'>
                    ⚠️ If this machine is not fixed immediately:
                </p>
                <ul style='color:#880000;'>
                    <li><b>{len(affected)} other machines</b>
                        will be forced to stop</li>
                    <li><b>{len(lines)} production line(s)</b>
                        will shut down</li>
                    <li>Estimated repair cost: <b>$23,000</b></li>
                    <li>Estimated time to failure:
                        <b>24 to 48 hours</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── SENSOR TRENDS AND DEPENDENCY ──
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown(
            "<div class='section-title'>📈 Sensor Readings Over Time</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "Select a machine to see its temperature "
            "and vibration history."
        )

        machine_options = {
            f"{MACHINES[m]['emoji']} {m} — {MACHINES[m]['name']}": m
            for m in machines
        }
        selected_label  = st.selectbox(
            "Choose a machine to inspect",
            list(machine_options.keys())
        )
        selected_machine = machine_options[selected_label]

        fig = render_sensor_chart(sensor_logs, selected_machine)
        st.plotly_chart(fig, use_container_width=True)

        # Reading explanation
        risk = final_state["failure_probability"].get(
            selected_machine, 0
        )
        if risk >= 0.75:
            st.error(
                "🔴 This machine shows DANGEROUS readings. "
                "Temperature or vibration is way above safe limits!"
            )
        elif risk >= 0.40:
            st.warning(
                "🟡 This machine shows ELEVATED readings. "
                "Keep monitoring closely."
            )
        else:
            st.success(
                "🟢 This machine is showing NORMAL readings. "
                "No action needed."
            )

    with col_right:
        st.markdown(
            "<div class='section-title'>🔗 Machine Connection Map</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "This map shows how machines depend on each other. "
            "If a red machine fails, everything connected to it stops."
        )

        fig = render_dependency_chart(final_state["graph_context"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div class='info-box'>
            <b>🔴 Red dot</b> = Machine that is failing<br>
            <b>🔵 Blue dot</b> = Healthy machine<br>
            <b>🟣 Purple dot</b> = Production line<br>
            <b>Lines between dots</b> = They depend on each other
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── RESULTS TABS ──
    st.markdown(
        "<div class='section-title'>📋 Detailed AI Analysis</div>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Simple Summary",
        "🔍 Why is it Failing?",
        "🔧 What to Do?",
        "📊 Full Data Table"
    ])

    with tab1:
        st.markdown("### 📋 Summary for Management")
        st.markdown(
            "This is written in simple language "
            "so anyone can understand it."
        )
        st.markdown(final_state["executive_summary"])

    with tab2:
        st.markdown("### 🔍 Root Cause — Why is the Machine Failing?")
        st.markdown(
            "This is the technical analysis of "
            "what went wrong and why."
        )
        st.markdown(final_state["root_cause_analysis"])

    with tab3:
        st.markdown("### 🔧 Maintenance Plan — Step by Step Actions")
        st.markdown(
            "Follow these steps to fix the problem "
            "and prevent it happening again."
        )
        st.markdown(final_state["maintenance_plan"])

    with tab4:
        st.markdown("### 📊 Machine Risk Score Table")

        risk_data = []
        for machine_id, info in MACHINES.items():
            prob         = final_state["failure_probability"].get(
                machine_id, 0
            )
            status_text, _, _ = get_status(prob)
            risk_data.append({
                "Machine ID":    machine_id,
                "Machine Name":  info["name"],
                "Type":          info["type"],
                "Location":      info["location"],
                "Vendor":        info["vendor"],
                "Risk Score":    f"{prob*100:.0f}%",
                "Health Status": status_text
            })

        st.dataframe(
            pd.DataFrame(risk_data),
            use_container_width = True,
            hide_index          = True
        )

        st.markdown("---")

        # Download button
        report_text = f"""
FACTORY HEALTH MONITOR REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

EXECUTIVE SUMMARY
{final_state['executive_summary']}

ROOT CAUSE ANALYSIS
{final_state['root_cause_analysis']}

MAINTENANCE PLAN
{final_state['maintenance_plan']}

MACHINE RISK SCORES
{'='*50}
"""
        for machine_id, info in MACHINES.items():
            prob = final_state["failure_probability"].get(machine_id, 0)
            status_text, _, _ = get_status(prob)
            report_text += (
                f"{machine_id} — {info['name']}: "
                f"{prob*100:.0f}% {status_text}\n"
            )

        st.download_button(
            label     = "📥 Download Full Report as Text File",
            data      = report_text,
            file_name = f"factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime      = "text/plain",
            use_container_width = True
        )


if __name__ == "__main__":
    main()