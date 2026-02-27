# reports/report_generator.py

from datetime import datetime

def save_report(state: dict):
    """Saves the full analysis to a text file"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"maintenance_report_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:

        f.write("=" * 60 + "\n")
        f.write("  SMART MANUFACTURING DOWNTIME INTELLIGENCE REPORT\n")
        f.write(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        f.write("📋 EXECUTIVE SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(state["executive_summary"] + "\n\n")

        f.write("🔍 ROOT CAUSE ANALYSIS\n")
        f.write("-" * 40 + "\n")
        f.write(state["root_cause_analysis"] + "\n\n")

        f.write("🔧 MAINTENANCE PLAN\n")
        f.write("-" * 40 + "\n")
        f.write(state["maintenance_plan"] + "\n\n")

        f.write("📊 MACHINE RISK SCORES\n")
        f.write("-" * 40 + "\n")
        for machine, prob in state["failure_probability"].items():
            bar   = "█" * int(prob * 20)
            empty = "░" * (20 - int(prob * 20))
            risk  = "🔴 CRITICAL" if prob >= 0.75 else (
                    "🟡 WARNING"  if prob >= 0.40 else
                    "🟢 NORMAL")
            f.write(f"{machine}: [{bar}{empty}] "
                    f"{prob*100:.0f}% {risk}\n")

    print(f"\n📄 Report saved → {filename}")
    return filename