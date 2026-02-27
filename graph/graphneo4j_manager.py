# graph/neo4j_manager.py

from neo4j import GraphDatabase
from config import Config

class Neo4jManager:
    """
    Builds a relationship map of all machines
    inside Neo4j Graph Database.
    """

    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )
        print("✅ Connected to Neo4j Database")

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")

    def create_machines(self):
        machines = [
            {
                "id": "M001", "name": "CNC Machine A",
                "type": "CNC", "plant": "Plant_North",
                "vendor": "Siemens", "status": "Running",
                "criticality": "High"
            },
            {
                "id": "M002", "name": "Conveyor Belt B",
                "type": "Conveyor", "plant": "Plant_North",
                "vendor": "ABB", "status": "Degrading",
                "criticality": "Critical"
            },
            {
                "id": "M003", "name": "Robotic Arm C",
                "type": "Robot", "plant": "Plant_South",
                "vendor": "FANUC", "status": "Running",
                "criticality": "High"
            },
            {
                "id": "M004", "name": "Hydraulic Press D",
                "type": "Press", "plant": "Plant_South",
                "vendor": "Bosch", "status": "Running",
                "criticality": "Medium"
            },
            {
                "id": "M005", "name": "Assembly Unit E",
                "type": "Assembly", "plant": "Plant_North",
                "vendor": "Siemens", "status": "Running",
                "criticality": "Critical"
            },
        ]

        with self.driver.session() as session:
            for m in machines:
                session.run("""
                    CREATE (:Machine {
                        id:          $id,
                        name:        $name,
                        type:        $type,
                        plant:       $plant,
                        vendor:      $vendor,
                        status:      $status,
                        criticality: $criticality
                    })
                """, **m)
        print(f"✅ Created {len(machines)} machine nodes")

    def create_production_lines(self):
        lines = [
            {"id": "PL001", "name": "Engine Assembly Line",
             "plant": "Plant_North"},
            {"id": "PL002", "name": "Body Welding Line",
             "plant": "Plant_South"},
            {"id": "PL003", "name": "Paint Shop Line",
             "plant": "Plant_North"},
        ]

        with self.driver.session() as session:
            for line in lines:
                session.run("""
                    CREATE (:ProductionLine {
                        id: $id, name: $name, plant: $plant
                    })
                """, **line)
        print(f"✅ Created {len(lines)} production line nodes")

    def create_relationships(self):
        with self.driver.session() as session:

            # Machine depends on machine
            dependencies = [
                ("M001", "M002", "High",     "Parts supply"),
                ("M005", "M002", "Critical", "Assembly feed"),
                ("M005", "M001", "High",     "Machined parts"),
                ("M004", "M003", "Medium",   "Positioning"),
            ]
            for a, b, impact, reason in dependencies:
                session.run("""
                    MATCH (a:Machine {id: $a})
                    MATCH (b:Machine {id: $b})
                    CREATE (a)-[:DEPENDS_ON {
                        impact: $impact,
                        reason: $reason
                    }]->(b)
                """, a=a, b=b, impact=impact, reason=reason)

            # Machine feeds production line
            feeds = [
                ("M001", "PL001", 1),
                ("M002", "PL001", 2),
                ("M005", "PL001", 3),
                ("M003", "PL002", 1),
                ("M004", "PL002", 2),
            ]
            for m, pl, seq in feeds:
                session.run("""
                    MATCH (m:Machine {id: $m})
                    MATCH (p:ProductionLine {id: $pl})
                    CREATE (m)-[:FEEDS_INTO {
                        sequence: $seq
                    }]->(p)
                """, m=m, pl=pl, seq=seq)

        print("✅ Created all relationships in Neo4j")

    def get_failure_impact(self, machine_id):
        """
        Key Query: If Machine X fails what else is affected?
        """
        with self.driver.session() as session:

            affected = session.run("""
                MATCH (a:Machine)-[:DEPENDS_ON*1..3]->
                      (f:Machine {id: $id})
                RETURN a.id   AS affected_id,
                       a.name AS affected_name,
                       a.criticality AS criticality
            """, id=machine_id)

            lines = session.run("""
                MATCH (m:Machine)-[:DEPENDS_ON*0..3]->
                      (f:Machine {id: $id})
                MATCH (m)-[:FEEDS_INTO]->(pl:ProductionLine)
                RETURN DISTINCT
                       pl.name  AS line_name,
                       pl.plant AS plant
            """, id=machine_id)

            return {
                "failing_machine":   machine_id,
                "affected_machines": [dict(r) for r in affected],
                "impacted_lines":    [dict(r) for r in lines]
            }

    def get_full_graph_summary(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN a.name      AS from_name,
                       type(r)     AS relationship,
                       b.name      AS to_name
            """)
            return [dict(r) for r in result]