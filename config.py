import tomllib

class Config:
    def __init__(self, data: dict[str]):
        self._data = data
    
    def get_neo4j_driver_kwargs(self):
        neo4j_data = self._data["neo4j"]
        return {
            "uri": neo4j_data["database_uri"],
            "auth": (neo4j_data["username"], neo4j_data["password"])
        }
    
    def get_neo4j_database_name(self):
        neo4j_data = self._data["neo4j"]
        return neo4j_data["database_name"]

def load_config(toml_path: str = "config.toml"):
    with open(toml_path, mode="rb") as fp:
        return Config(tomllib.load(fp))
