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
            f'{NOTEBOOK_BASE_DIR}/01-Getting-Started/01-About-the-Neptune-Notebook.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Getting-Started/02-Using-Gremlin-to-Access-the-Graph.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Getting-Started/03-Using-RDF-and-SPARQL-to-Access-the-Graph.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Getting-Started/04-Social-Network-Recommendations-with-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/01-Getting-Started/05-Dining-By-Friends-in-Amazon-Neptune.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/Air-Routes-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/Air-Routes-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/Air-Routes-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/Blog Workbench Visualization.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/EPL-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/EPL-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/EPL-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/02-Visualization/Grouping-and-Appearance-Customization-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/00-Sample-Applications-Overview.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/01-Fraud-Graphs/01-Building-a-Fraud-Graph-Application.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/02-Knowledge-Graphs/Building-a-Knowledge-Graph-Application-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/02-Knowledge-Graphs/Building-a-Knowledge-Graph-Application-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/03-Identity-Graphs/01-Building-an-Identity-Graph-Application.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/03-Identity-Graphs/02-Data-Modeling-for-Identity-Graphs.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/03-Identity-Graphs/03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL/03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/04-Security-Graphs/01-Building-a-Security-Graph-Application-with-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/04-Security-Graphs/01-Building-a-Security-Graph-Application-with-openCypher.ipynb',
            f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/05-Healthcare-and-Life-Sciences-Graphs/01-Modeling-Molecular-Structures-as-Graph-Data-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-00-Getting-Started-with-Neptune-ML-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-01-Introduction-to-Node-Classification-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-02-Introduction-to-Node-Regression-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-03-Introduction-to-Link-Prediction-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-04-Introduction-to-Edge-Classification-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-05-Introduction-to-Edge-Regression-Gremlin.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-SPARQL/Neptune-ML-00-Getting-Started-with-Neptune-ML-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-SPARQL/Neptune-ML-01-Introduction-to-Object-Classification-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-SPARQL/Neptune-ML-02-Introduction-to-Object-Regression-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Neptune-ML-SPARQL/Neptune-ML-03-Introduction-to-Link-Prediction-SPARQL.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Sample-Applications/01-People-Analytics/People-Analytics-using-Neptune-ML.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Sample-Applications/02-Job-Recommendation-Text-Encoding.ipynb',
            f'{NOTEBOOK_BASE_DIR}/04-Machine-Learning/Sample-Applications/03-Real-Time-Fraud-Detection-Using-Inductive-Inference.ipynb',
            f'{NOTEBOOK_BASE_DIR}/05-Data-Science/00-Identifying-Fraud-Rings-Using-Social-Network-Analytics.ipynb',
            f'{NOTEBOOK_BASE_DIR}/05-Data-Science/01-Identifying-1st-Person-Synthetic-Identity-Fraud-Using-Graph-Similarity.ipynb',            
            f'{NOTEBOOK_BASE_DIR}/05-Data-Science/02-Logistics-Analysis-using-a-Transportation-Network.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/01-SPARQL/01-SPARQL-Basics.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/02-openCypher/01-Basic-Read-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/02-openCypher/02-Variable-Length-Paths.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/02-openCypher/03-Ordering-Functions-Grouping.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/02-openCypher/04-Creating-Updating-Delete-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/02-openCypher/openCypher-Exercises-Answer-Key.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/03-Gremlin/01-Basic-Read-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/03-Gremlin/02-Loops-Repeats.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/03-Gremlin/03-Ordering-Functions-Grouping.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/03-Gremlin/04-Creating-Updating-Deleting-Queries.ipynb',
            f'{NOTEBOOK_BASE_DIR}/06-Language-Tutorials/03-Gremlin/Gremlin-Exercises-Answer-Sheet.ipynb']
        notebook_paths = get_all_notebooks_paths()
        expected_paths.sort()
        notebook_paths.sort()

        self.assertEqual(len(expected_paths), len(notebook_paths))
        for i in range(len(expected_paths)):
            self.assertEqual(expected_paths[i], notebook_paths[i])

    def test_validate_notebooks_have_no_output(self):
        notebooks = get_all_notebooks_paths()
        for n in notebooks:
            with open(n, 'r') as notebook_file:
                file_content = notebook_file.read()
                nb_content = json.loads(file_content)
                for cell in nb_content['cells']:
                    if 'cell_type' in cell and cell['cell_type'] == 'code':
                        self.assertEqual(0, len(cell['outputs']))

    def test_readme_and_overview_match(self):
        notebook_file_path = f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/00-Sample-Applications-Overview.ipynb'
        readme_file_path = f'{NOTEBOOK_BASE_DIR}/03-Sample-Applications/README.md'

        with open(notebook_file_path, 'r') as notebook_file:
            notebook_js = json.load(notebook_file)

        with open(readme_file_path, 'r') as readme_file:
            readme_content = readme_file.read()

        notebook_content = ''
        notebook_content = notebook_content.join(notebook_js['cells'][0]['source'])

        self.assertEqual(notebook_js['cells'][0]['cell_type'], 'markdown')
        self.assertEqual(readme_content, notebook_content)
