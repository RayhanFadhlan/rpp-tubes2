from config import load_config
from neo4j import GraphDatabase as Neo4jDatabase

class GraphDatabaseDriver:
    def __init__(self, toml_config_path: str = "config.toml"):
        self._config = load_config(toml_config_path)
        self._driver = None
        self._last_result_details = None

    def __enter__(self):
        kwargs = self._config.get_neo4j_driver_kwargs()
        self._driver = Neo4jDatabase.driver(**kwargs)
        self._driver.verify_connectivity()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._driver:
            self._driver.close()

    def execute_query(self, query: str):
        database_name = self._config.get_neo4j_database_name()
        with self._driver.session(database=database_name) as session:
            self._last_result_details = session.run(query)
            return self._last_result_details.data()

    def get_last_result_details(self):
        return self._last_result_details.to_eager_result()
