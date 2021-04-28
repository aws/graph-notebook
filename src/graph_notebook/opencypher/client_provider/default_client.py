from abc import ABC, abstractmethod

from neo4j import GraphDatabase, Driver


class AbstractCypherClientProvider(ABC):
    @abstractmethod
    def get_driver(self, host: str, port: str, ssl: bool, user: str = 'neo4j', password: str = 'neo4j') -> GraphDatabase.driver:
        pass


class CypherClientProvider(AbstractCypherClientProvider):
    """
    CypherClientProvider is a client which will attempt to obtain a bolt
    connection to the configured endpoint without any authentication settings
    """

    def get_driver(self, host: str, port: str, ssl: bool, user: str = 'neo4j', password: str = 'neo4j') -> Driver:
        uri = f'bolt://{host}:{port}'
        driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=ssl)
        return driver
