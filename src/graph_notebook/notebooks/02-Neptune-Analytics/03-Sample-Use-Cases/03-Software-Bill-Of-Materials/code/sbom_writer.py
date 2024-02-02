import boto3
import json
import logging
import uuid
from itertools import islice
from enum import Enum


class BomType(Enum):
    CYDX = "cyclonedx"
    SPDX = "spdx"
    UNKNOWN = "unknown"


BATCH_SIZE = 200


class NodeLabels(Enum):
    DOCUMENT = "Document"
    COMPONENT = "Component"
    VULNERABILITY = "Vulnerability"
    REFERENCE = "Reference"


class EdgeLabels(Enum):
    DESCRIBES = "DESCRIBES"
    REFERS_TO = "REFERS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    DEPENDENCY_OF = "DEPENDENCY_OF"
    DESCRIBED_BY = "DESCRIBED_BY"
    CONTAINS = "CONTAINS"
    AFFECTS = "AFFECTS"


logger = logging.getLogger(__name__)


class NeptuneAnalyticsSBOMWriter:
    client = None
    graph_identifier = None

    def __init__(self, graph_identifier: str, region: str) -> None:
        self.client = boto3.client("neptune-graph", region_name=region)
        self.graph_identifier = graph_identifier

    def __determine_filetype(self, bom: str) -> BomType:
        if "spdxVersion" in bom:
            logging.info("Identified file as SPDX")
            return BomType.SPDX
        elif "bomFormat" in bom:
            logging.info("Identified file as CycloneDX")
            return BomType.CYDX
        else:
            logging.warning("Unknown SBOM format")
            return BomType.UNKNOWN

    def write_sbom(self, bom: str) -> bool:
        bom_type = self.__determine_filetype(bom)
        res = False
        if bom_type == BomType.CYDX:
            res = CycloneDXWriter(self.graph_identifier, self.client).write_document(
                bom
            )
        elif bom_type == BomType.SPDX:
            res = SPDXWriter(self.graph_identifier, self.client).write_document(bom)
        else:
            logging.warning("Unknown SBOM format")

        return res


class Writer:
    client = None
    graph_identifier = None
    batch_size = 200

    def __init__(self, graph_identifier: str, client: boto3.client) -> None:
        self.client = client
        self.graph_identifier = graph_identifier

    def chunk(arr_range, arr_size):
        arr_range = iter(arr_range)
        return iter(lambda: tuple(islice(arr_range, arr_size)), ())

    def write_objects(
        self,
        objs: object,
        label: str,
        keyName: str,
        create_uuid_if_key_not_exists: bool = False,
        id: str = None,
    ):
        params = []
        logging.info(f"Writing {label} nodes")
        if len(objs) == 0:
            return

        query = (
            """
                UNWIND $props as p
                MERGE (s:"""
            + label
            + """ {`~id`: p.__id})
                SET """
            + self.__create_property_map_str(objs[0])
        )

        for o in objs:
            if keyName in o:
                params.append(
                    {
                        "__id": f"{label}_{o[keyName]}",
                        **self.__cleanup_map(o),
                    }
                )
            elif create_uuid_if_key_not_exists:
                params.append(
                    {
                        "__id": f"{label}_{uuid.uuid4()}",
                        **self.__cleanup_map(o),
                    }
                )

            elif id:
                params.append(
                    {
                        "__id": id,
                        **self.__cleanup_map(o),
                    }
                )
            else:
                raise AttributeError(
                    f"The object {o} does not contain the key {keyName}"
                )

        arr_range = iter(params)
        chunks = iter(lambda: tuple(islice(arr_range, self.batch_size)), ())
        for chunk in chunks:
            # This should not be needed but due to an issue with duplicate maps we have to guarantee uniqeness
            res = list(map(dict, set(tuple(sorted(sub.items())) for sub in chunk)))

            self.execute_query({"props": res}, query)

    def write_rel(self, rels: list, label: str):
        logging.info(f"Writing {label} edges")
        if len(rels) == 0:
            return

        query = (
            """                
                    UNWIND $rels as r
                    MATCH (from {`~id`: r.fromId})
                    MATCH (to {`~id`: r.toId})
                    MERGE (from)-[s:"""
            + label
            + """]->(to) """
        )

        arr_range = iter(rels)
        chunks = iter(lambda: tuple(islice(arr_range, self.batch_size)), ())
        for chunk in chunks:
            # This should not be needed but due to an issue with duplicate maps we have to guarantee uniqeness
            res = list(map(dict, set(tuple(sorted(sub.items())) for sub in chunk)))
            self.execute_query({"rels": res}, query)

    def write_rel_match_on_property(
        self, rels: list, label: str, from_property: str, to_property: str
    ):
        logging.info(f"Writing {label} edges")
        if len(rels) == 0:
            return

        query = (
            """                
                    UNWIND $rels as r
                    MATCH (from {`"""
            + from_property
            + """`: r.from})
                    MATCH (to {`"""
            + to_property
            + """`: r.to})
                    MERGE (from)-[s:"""
            + label
            + """]->(to) """
        )

        arr_range = iter(rels)
        chunks = iter(lambda: tuple(islice(arr_range, self.batch_size)), ())
        for chunk in chunks:
            # This should not be needed but due to an issue with duplicate maps we have to guarantee uniqeness
            res = list(map(dict, set(tuple(sorted(sub.items())) for sub in chunk)))
            self.execute_query({"rels": res}, query)

    def execute_query(self, params, query):
        resp = self.client.execute_query(
            queryString=query,
            parameters=params,
            language="OPEN_CYPHER",
            graphIdentifier=self.graph_identifier,
        )
        if not resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            print(f"An error occurred on query: {query}")
        return resp

    def __cleanup_map(self, props: dict) -> str:
        """
        This should remove all the lists and dict properties from the map
        """
        result = {}
        for k in props.keys():
            if not isinstance(props[k], list) and not isinstance(props[k], dict):
                result[k] = props[k]
        return result

    def __create_property_map_str(self, props: dict, exclude_list: list = []) -> str:
        """
        This should not be needed but there is a bug in P8 that prevents Maps from working
        """
        result = []
        for k in props.keys():
            if k not in exclude_list:
                if type(props[k]) is None:
                    result.append(f"s.`{k}` = null")
                elif isinstance(props[k], list) or isinstance(props[k], dict):
                    pass
                else:
                    result.append(f"s.`{k}` = p.`{k}`")
        return ",".join(result)


class CycloneDXWriter(Writer):
    def write_document(self, bom):
        logging.info("Writing bom metadata")
        document_id = self.__write_bom(bom)

        if "components" in bom:
            self.__write_components(bom["components"], document_id)
        if "dependencies" in bom:
            self.__write_dependencies(bom["dependencies"], document_id)
        if "vulnerabilities" in bom:
            self.__write_vulnerabilities(bom["vulnerabilities"])
        return True

    def __write_bom(self, bom):
        if "serialNumber" in bom:
            document_id = f"{NodeLabels.DOCUMENT.value}_{bom['serialNumber']}"
        else:
            document_id = f"{NodeLabels.DOCUMENT.value}_{uuid.uuid4()}"

        document = {**bom, **bom["metadata"], **bom["metadata"]["component"]}

        # Do mappings from Cyclone DX to more generic name
        document["spec_version"] = document.pop("specVersion")
        document["created_timestamp"] = document.pop("timestamp")

        self.write_objects([document], NodeLabels.DOCUMENT.value, None, id=document_id)

        return document_id

    def __write_components(self, components: list, document_id: str):
        self.write_objects(components, NodeLabels.COMPONENT.value, "name")
        describes_edges = [
            {"fromId": document_id, "toId": f"{NodeLabels.COMPONENT.value}_{c['name']}"}
            for c in components
        ]
        self.write_rel(describes_edges, EdgeLabels.DESCRIBES.value)

        refs = []
        refers_to_edges = []
        for c in components:
            if "externalReferences" in c:
                refs.extend(c["externalReferences"])
                refers_to_edges.extend(
                    [
                        {
                            "fromId": f"{NodeLabels.COMPONENT.value}_{c['name']}",
                            "toId": f"{NodeLabels.REFERENCE.value}_{r['url']}",
                        }
                        for r in c["externalReferences"]
                    ]
                )
        self.write_objects(refs, NodeLabels.REFERENCE.value, "url")
        self.write_rel(refers_to_edges, EdgeLabels.REFERS_TO.value)

    def __write_dependencies(self, dependencies: list, document_id: str):
        deps = []
        depends_on_edges = []
        for d in dependencies:
            if "dependsOn" in d:
                deps.extend([{"ref": dep} for dep in d["dependsOn"]])
                depends_on_edges.extend(
                    [
                        {
                            "to": dep,
                            "from": d["ref"],
                        }
                        for dep in d["dependsOn"]
                    ]
                )

        self.write_rel_match_on_property(
            depends_on_edges, EdgeLabels.DEPENDS_ON.value, "purl", "purl"
        )

    def __write_vulnerabilities(self, vulnerabilities: list):
        affects_edges = []
        vuls = []
        for v in vulnerabilities:
            if "ratings" in v and len(v["ratings"]) > 0:
                vuls.append({**v, **v["ratings"][0]})
            for a in v["affects"]:
                affects_edges.append(
                    {
                        "from": v["id"],
                        "to": a["ref"],
                    }
                )

        self.write_objects(vuls, NodeLabels.VULNERABILITY.value, "id")
        self.write_rel_match_on_property(
            affects_edges, EdgeLabels.AFFECTS.value, "id", "bom-ref"
        )


class SPDXWriter(Writer):
    def write_document(self, bom):
        logging.info("Writing bom metadata")

        document_id = self.__write_bom(bom)

        if "packages" in bom:
            logging.info("Writing packages as components")
            self.__write_packages(bom["packages"])

        if "relationships" in bom:
            logging.info("Writing relationships")
            self.__write_relationships(bom["relationships"], document_id)

        return True

    def __write_bom(self, bom):
        document_id = f"{NodeLabels.DOCUMENT.value}_{uuid.uuid4()}"
        document = {**bom, **bom["creationInfo"]}

        # Do mappings from Cyclone DX to more generic name
        document["specVersion"] = document.pop("spdxVersion")
        document["createdTimestamp"] = document.pop("created")
        document["bomFormat"] = "SPDX"

        self.write_objects([document], NodeLabels.DOCUMENT.value, None, id=document_id)

        return document_id

    def __write_packages(self, packages: list):
        for c in packages:
            if "externalRefs" in c:
                for r in c["externalRefs"]:
                    if r["referenceType"] == "purl":
                        c["purl"] = r["referenceLocator"]
                        break

        self.write_objects(packages, NodeLabels.COMPONENT.value, "name")

        logging.info("Writing component -> externalReferences")
        refs = []
        refers_to_edges = []
        for c in packages:
            if "externalRefs" in c:
                refs.extend(c["externalRefs"])
                refers_to_edges.extend(
                    [
                        {
                            "fromId": f"{NodeLabels.COMPONENT.value}_{c['name']}",
                            "toId": f"{NodeLabels.REFERENCE.value}_{r['referenceLocator']}",
                        }
                        for r in c["externalRefs"]
                    ]
                )
        self.write_objects(refs, NodeLabels.REFERENCE.value, "referenceLocator")
        self.write_rel(refers_to_edges, EdgeLabels.REFERS_TO.value)

    def __write_relationships(self, relationships: list, document_id: str):
        logging.info("Writing relationship edges")
        describes_edges = []
        depends_on_edges = []
        dependency_of_edges = []
        described_by_edges = []
        contains_edges = []
        for d in relationships:
            if d["relationshipType"] == "DESCRIBES":
                describes_edges.append(
                    {
                        "to": d["relatedSpdxElement"],
                        "from": document_id,
                    }
                )
            elif d["relationshipType"] == "DEPENDS_ON":
                depends_on_edges.append(
                    {
                        "to": d["relatedSpdxElement"],
                        "from": document_id,
                    }
                )
            elif d["relationshipType"] == "DEPENDENCY_OF":
                dependency_of_edges.append(
                    {
                        "to": d["relatedSpdxElement"],
                        "from": document_id,
                    }
                )
            elif d["relationshipType"] == "DESCRIBED_BY":
                described_by_edges.append(
                    {
                        "to": d["relatedSpdxElement"],
                        "from": document_id,
                    }
                )
            elif d["relationshipType"] == "CONTAINS":
                contains_edges.append(
                    {
                        "to": d["relatedSpdxElement"],
                        "from": document_id,
                    }
                )
            else:
                logging.warning(f"Unknown relationship type {d['relationshipType']}")
                continue

        if len(describes_edges) > 0:
            self.write_rel_match_on_property(
                describes_edges, EdgeLabels.DESCRIBES.value, "~id", "SPDXID"
            )
        if len(depends_on_edges) > 0:
            self.write_rel_match_on_property(
                depends_on_edges, EdgeLabels.DEPENDS_ON.value, "~id", "SPDXID"
            )
        if len(dependency_of_edges) > 0:
            self.write_rel_match_on_property(
                dependency_of_edges, EdgeLabels.DEPENDS_ON.value, "~id", "SPDXID"
            )

        if len(described_by_edges) > 0:
            self.write_rel_match_on_property(
                described_by_edges, EdgeLabels.DEPENDS_ON.value, "~id", "SPDXID"
            )

        if len(contains_edges) > 0:
            self.write_rel_match_on_property(
                contains_edges, EdgeLabels.DEPENDS_ON.value, "~id", "SPDXID"
            )
