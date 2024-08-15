"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import unittest

from graph_notebook.notebooks.install import get_all_notebooks_paths, NOTEBOOK_BASE_DIR


class TestValidateAllNotebooks(unittest.TestCase):
    maxDiff = None

    def test_no_extra_notebooks(self):
        """
        hard-coded the expected paths for notebooks so that adding new ones is intentional.
        """

        expected_paths = [
            f'{NOTEBOOK_BASE_DIR}/Overview.ipynb',
            f'{NOTEBOOK_BASE_DIR}/About-the-Neptune-Notebook.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/01-Getting-Started/01-About-the-Neptune-Notebook.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/01-Getting-Started/02-Using-Gremlin-to-Access-the-Graph.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/01-Getting-Started/03-Using-RDF-and-SPARQL-to-Access-the-Graph.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/01-Getting-Started/04-Social-Network-Recommendations-with-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/01-Getting-Started/05-Dining-By-Friends-in-Amazon-Neptune.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/Air-Routes-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/Air-Routes-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/Air-Routes-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/Blog Workbench Visualization.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/EPL-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/EPL-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/EPL-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/02-Visualization/Grouping-and-Appearance-Customization-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/00-Sample-Applications-Overview.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/01-Fraud-Graphs/01-Building-a-Fraud-Graph-Application.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/02-Knowledge-Graphs/Building-a-Knowledge-Graph-Application-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/02-Knowledge-Graphs/Building-a-Knowledge-Graph-Application-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/03-Identity-Graphs/01-Building-an-Identity-Graph-Application.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/03-Identity-Graphs/02-Data-Modeling-for-Identity-Graphs.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/03-Identity-Graphs/03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL/03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/04-Security-Graphs/01-Building-a-Security-Graph-Application-with-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/04-Security-Graphs/01-Building-a-Security-Graph-Application-with-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/05-Healthcare-and-Life-Sciences-Graphs/01-Modeling-Molecular-Structures-as-Graph-Data-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/06-Data-Science-Samples/01-Identifying-Fraud-Rings-Using-Social-Network-Analytics.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/06-Data-Science-Samples/02-Identifying-1st-Person-Synthetic-Identity-Fraud-Using-Graph-Similarity.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/06-Data-Science-Samples/03-Logistics-Analysis-using-a-Transportation-Network.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/07-Games-Industry-Graphs/01-Building-a-Social-Network-for-Games-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/01-Getting-Started/01-Getting-Started-With-Neptune-Analytics.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/01-Getting-Started-With-Graph-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/02-Path-Finding-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/03-Centrality-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/04-Community-Detection-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/05-Similarity-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/02-Graph-Algorithms/06-Vector-Similarity-Algorithms.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/Overview.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/01-FinTech/01-Fraud-Ring-Identifcation.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/02-Investment-Analysis/01-EDGAR-Competitor-Analysis-using-Knowledge-Graph-Graph-Algorithms-and-Vector-Search.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/03-Software-Bill-Of-Materials/00-Intro-to-Software-Bill-Of-Materials.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/03-Software-Bill-Of-Materials/01-SBOM-Dependency-Analysis.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/03-Sample-Use-Cases/03-Software-Bill-Of-Materials/02-SBOM-Vulnerability-Analysis.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/04-OpenCypher-Over-RDF/01-Air-Routes.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Neptune-Analytics/04-OpenCypher-Over-RDF/02-Air-Routes-GeoNames.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/01-Getting-Started-with-Neptune-ML-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/02-Introduction-to-Node-Classification-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/03-Introduction-to-Node-Regression-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/04-Introduction-to-Link-Prediction-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/05-Introduction-to-Edge-Classification-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/01-Gremlin/06-Introduction-to-Edge-Regression-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/02-SPARQL/Neptune-ML-00-Getting-Started-with-Neptune-ML-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/02-SPARQL/Neptune-ML-01-Introduction-to-Object-Classification-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/02-SPARQL/Neptune-ML-02-Introduction-to-Object-Regression-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/02-SPARQL/Neptune-ML-03-Introduction-to-Link-Prediction-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/01-People-Analytics/People-Analytics-using-Neptune-ML.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/02-Job-Recommendation-Text-Encoding.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/03-Real-Time-Fraud-Detection-Using-Inductive-Inference.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/1a-Use-case.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/1b-Graph_init.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/2a-GraphQueryGremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/2b-GraphQueryLLM.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/3a-TransductiveMode-CellPrediction.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Neptune-ML/03-Sample-Applications/04-Telco-Networks/3b-InductiveModeCell-Prediction.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/01-Gremlin/01-Basic-Read-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/01-Gremlin/02-Loops-Repeats.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/01-Gremlin/03-Ordering-Functions-Grouping.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/01-Gremlin/04-Creating-Updating-Deleting-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/01-Gremlin/Gremlin-Exercises-Answer-Sheet.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/02-openCypher/01-Basic-Read-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/02-openCypher/02-Variable-Length-Paths.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/02-openCypher/03-Ordering-Functions-Grouping.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/02-openCypher/04-Creating-Updating-Delete-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/02-openCypher/openCypher-Exercises-Answer-Key.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Language-Tutorials/03-SPARQL/01-SPARQL-Basics.ipynb']
        notebook_paths = get_all_notebooks_paths()
        expected_paths.sort()
        notebook_paths.sort()

        self.assertEqual(len(expected_paths), len(notebook_paths))
        for i in range(len(expected_paths)):
            self.assertEqual(expected_paths[i], notebook_paths[i])

    def test_validate_notebooks_have_no_output(self):
        notebooks = get_all_notebooks_paths()
        for n in notebooks:
            print(f"Notebook: {n}")
            with open(n, 'r') as notebook_file:
                file_content = notebook_file.read()
                nb_content = json.loads(file_content)
                for cell in nb_content['cells']:
                    if 'cell_type' in cell and cell['cell_type'] == 'code':
                        self.assertEqual(0, len(cell['outputs']))
            print("Passed!")

    def test_readme_and_overview_match(self):
        notebook_file_path = f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/00-Sample-Applications-Overview.ipynb'
        readme_file_path = f'{NOTEBOOK_BASE_DIR}/01-Neptune-Database/03-Sample-Applications/README.md'

        with open(notebook_file_path, 'r') as notebook_file:
            notebook_js = json.load(notebook_file)

        with open(readme_file_path, 'r') as readme_file:
            readme_content = readme_file.read()

        notebook_content = ''
        notebook_content = notebook_content.join(notebook_js['cells'][0]['source'])

        self.assertEqual(notebook_js['cells'][0]['cell_type'], 'markdown')
        self.assertEqual(readme_content, notebook_content)
