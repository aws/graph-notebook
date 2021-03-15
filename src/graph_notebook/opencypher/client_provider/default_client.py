from abc import ABC, abstractmethod

from py2neo import Graph
from neo4j import GraphDatabase


class AbstractCypherClientProvider(ABC):
    @abstractmethod
    def get_driver(self, host: str, port: str, ssl: bool) -> GraphDatabase.driver:
        pass


class CypherClientProvider(AbstractCypherClientProvider):
    """
    CypherClientProvider is a client which will attempt to obtain a bolt
    connection to the configured endpoint without any authentication settings
    """

    def get_driver(self, host: str, port: str, ssl: bool) -> Graph:
        uri = f'bolt://{host}:{port}'
        driver = GraphDatabase.driver(uri, auth=('neo4j', 'password'), encrypted=ssl)
        return driver
