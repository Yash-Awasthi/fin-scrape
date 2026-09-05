"""
Thin wrapper around the Neo4j driver. Reads connection details from
environment variables so credentials never live in code:
  NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""
import os
from neo4j import GraphDatabase


def get_driver():
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(2409cf0a, kzjNubEAj4HOtwT6IJZvHCf7DFyb-FctIegO9Xbna3k))


def setup_schema(driver):
    """Run once — safe to re-run (IF NOT EXISTS)."""
    def _setup(tx):
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Route) REQUIRE r.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE")

    with driver.session() as session:
        session.execute_write(_setup)


def ingest_routes(driver, routes: dict):
    def _ingest(tx, routes):
        for route_name, locations in routes.items():
            tx.run("MERGE (r:Route {name: $route_name})", route_name=route_name)
            for loc in locations:
                tx.run(
                    """
                    MERGE (l:Location {name: $loc})
                    MERGE (r:Route {name: $route_name})
                    MERGE (r)-[:PASSES_THROUGH]->(l)
                    """,
                    loc=loc, route_name=route_name,
                )

    with driver.session() as session:
        session.execute_write(_ingest, routes)


def get_checkpoint(driver, checkpoint_id="gdelt_ingest"):
    with driver.session() as session:
        result = session.run(
            "MATCH (c:Checkpoint {id: $id}) RETURN c.last_file AS last_file",
            id=checkpoint_id,
        )
        row = result.single()
        return row["last_file"] if row else None


def set_checkpoint(driver, filename, checkpoint_id="gdelt_ingest"):
    with driver.session() as session:
        session.run(
            """
            MERGE (c:Checkpoint {id: $id})
            SET c.last_file = $filename, c.updated_at = datetime()
            """,
            id=checkpoint_id, filename=filename,
        )
