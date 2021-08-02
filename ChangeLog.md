# graph-notebook Change Log

Starting with v1.31.6, this file will contain a record of major features and updates made in each release of graph-notebook.

## Upcoming
- Gremlin visualization bugfixes ([Link to PR](https://github.com/aws/graph-notebook/pull/166))

## Release 3.0.2 (July 29, 2021)

- Add new Knowledge Graph use case notebook for openCypher usage ([Link to PR](https://github.com/aws/graph-notebook/pull/161))
- Fixed incorrect visualizations of some Gremlin results returned by valueMap ([Link to PR](https://github.com/aws/graph-notebook/pull/165))
- Fixed error with Gremlin visualizer incorrectly identifying some query results as elementMaps ([Link to PR](https://github.com/aws/graph-notebook/pull/158))
- Pin RDFLib version in README ([Link to PR](https://github.com/aws/graph-notebook/pull/162))
- Fixed inconsistent node tooltips in openCypher visualizations ([Link to PR](https://github.com/aws/graph-notebook/pull/163))

## Release 3.0.1 (July 28, 2021)

**openCypher Support**:

With the release of support for the openCypher query language in Amazon Neptune's lab mode, graph-notebook can now be used to execute and visualize openCypher queries with any compatible graph database.

Two new magic commands have been added: 
- `%%oc`/`%%opencypher` 
- `%%oc_status`/`%%opencypher_status`

These openCypher magic commands inherit the majority of the query and visualization customization features that are already available in the Gremlin and SPARQL magics.

For more detailed information and examples of how you can execute and visualize openCypher queries through graph-notebook, please refer to the new `Air-Routes-openCypher` and `EPL-openCypher` sample notebooks.

([Link to PR](https://github.com/aws/graph-notebook/pull/153))

**Other major updates**:
- Added visualization support for elementMap Gremlin step ([Link to PR](https://github.com/aws/graph-notebook/pull/140))
- Added support for additional customization of edge node labels in Gremlin ([Link to PR](https://github.com/aws/graph-notebook/pull/132))
- Refactored %load form display code for flexibility; fixes some descriptions being cut off
- Updated Neptune ML notebooks, utils, and pretrained models config ([Link to PR](https://github.com/aws/graph-notebook/pull/153))
- Added support for `modeltransform` commands in `%neptune_ml` ([Link to PR](https://github.com/aws/graph-notebook/pull/153))
- Overhauled Gremlin visualization notebooks with example usage of new customization options and elementMap step ([Link to PR](https://github.com/aws/graph-notebook/pull/153))
- Added new notebook to explain Identity Graph data modeling ([Link to PR](https://github.com/aws/graph-notebook/pull/154))

**Minor updates**:
- Included index operations metrics in metadata results tab for Gremlin Profile queries([Link to PR](https://github.com/aws/graph-notebook/pull/150))
- Updated SPARQL EPL seed dataset file ([Link to PR](https://github.com/aws/graph-notebook/pull/134))
- Updated documentation on using `%%graph_notebook_config` with an IAM enabled Neptune cluster ([Link to PR](https://github.com/aws/graph-notebook/pull/136))
  
**Bugfixes**:
- Fixed improper handling of Blazegraph status response ([Link to PR](https://github.com/aws/graph-notebook/pull/137))
- Fixed Gremlin node tooltips being displayed incorrectly ([Link to PR](https://github.com/aws/graph-notebook/pull/139))
- Fixed bug in using Gremlin explain/profile with large result sets ([Link to PR](https://github.com/aws/graph-notebook/pull/141))
- Pinned RDFLib version ([Link to PR](https://github.com/aws/graph-notebook/pull/151))

## Release 2.1.4 (June 27, 2021)
- Added support for additional customization of graph node labels in Gremlin ([Link to PR](https://github.com/aws/graph-notebook/pull/127))

## Release 2.1.3 (June 18, 2021)
- Added support for dictionary value access in variable injection([Link to PR](https://github.com/aws/graph-notebook/pull/126))

## Release 2.1.2 (May 10, 2021)

- Pinned gremlinpython to `<3.5.*` ([Link to PR](https://github.com/aws/graph-notebook/pull/123))
- Added support for notebook variables in Sparql/Gremlin magic queries ([Link to PR](https://github.com/aws/graph-notebook/pull/113))
- Added support for grouping by different properties per label in Gremlin ([Link to PR](https://github.com/aws/graph-notebook/pull/115))
- Fixed missing Boto3 dependency in setup.py ([Link to PR](https://github.com/aws/graph-notebook/pull/118))
- Updated %load execution time to HH:MM:SS format if over a minute ([Link to PR](https://github.com/aws/graph-notebook/pull/121))

## Release 2.1.1 (April 22, 2021)

- Fixed bug in `%neptune_ml export ...` logic where the iam setting for the exporter endpoint wasn't getting picked up properly

## Release 2.1.0 (April 15, 2021)

- Added support for Mode, queueRequest, and Dependencies parameters when running %load command ([Link to PR](https://github.com/aws/graph-notebook/pull/91))
- Added support for list and dict as map keys in Python Gremlin ([Link to PR](https://github.com/aws/graph-notebook/pull/100))
- Refactored modules that call to Neptune or other SPARQL/Gremlin endpoints to use a unified client object ([Link to PR](https://github.com/aws/graph-notebook/pull/104))
- Added an additional notebook under [02-Visualization](src/graph_notebook/notebooks/02-Visualization) demonstrating how to use the visualzation grouping and coloring options in Gremlin. ([Link to PR](https://github.com/aws/graph-notebook/pull/107))
- Added metadata output tab for magic queries ([Link to PR](https://github.com/aws/graph-notebook/pull/108))

## Release 2.0.12 (Mar 25, 2021)

 - Added default parameters for `get_load_status` ([Link to PR](https://github.com/aws/graph-notebook/pull/96))
 - Added ipython as a dependency in `setup.py` ([Link to PR](https://github.com/aws/graph-notebook/pull/95))
 - Added parameters in `load_status` for `details`, `errors`, `page`, and `errorsPerPage` ([Link to PR](https://github.com/aws/graph-notebook/pull/88))

## Release 2.0.10 (Mar 18, 2021)

- Print execution time when running %load command ([Link to PR](https://github.com/aws/graph-notebook/pull/82))

## Release 2.0.9 (Mar 3, 2021)

- Fixed issue where --ignore-groups was not being honored [Link to PR](https://github.com/aws/graph-notebook/pull/66)
- Changed SPARQL path parameter in %%graph-notebook-config command to no longer append /sparql to the end, which should give support to more SPARQL 1.1 endpoints [Link to PR](https://github.com/aws/graph-notebook/pull/75)

#### New Notebooks and Datasets
Added new sample application notebooks and `%seed` datasets under [03-Sample-Applications](src/graph_notebook/notebooks/03-Sample-Applications) for the following use cases: 
- Fraud Graph
- Knowledge Graph
- Identity Graph

[Link to PR](https://github.com/aws/graph-notebook/pull/77)

## Release 2.0.7 (Feb 1, 2021)

- Added  "What’s Next" sections to 01-Getting-Started notebooks to suggest users to relevant notebook tutorials [Link to PR](https://github.com/aws/graph-notebook/pull/60)

## Release 2.0.6 (Jan 28, 2021)

- Added missing __init__ to notebook directories to they get installed correctly
- Updated list of available magics in notebook documentation [Link to PR](https://github.com/aws/graph-notebook/pull/56)

## Release 2.0.5 (Jan 8, 2021)

#### Gremlin Visualization
- Enhanced Gremlin Visualization output to group vertices and color-code them based on groups. When not specified it will group by the label (if it exists). You can also specify the property to groupby using the switch --groupby or -g followed by the property name [Link to PR](https://github.com/aws/graph-notebook/pull/15)
- Added the functionality to sort the values in the details box by key
- Updated Air-Routes-Visualization notebook to discuss the group by functionality
#### Neptune ML
- Added new tutorial notebooks for Neptune ML functionality [Link to PR](https://github.com/aws/graph-notebook/pull/53)

## Release 2.0.3 (Dec 29, 2020)

This release features integration with the Neptune ML feature set in AWS Neptune. [Link to PR](https://github.com/aws/graph-notebook/pull/48)

- Added helper library to perform Sigv4 signing for %neptune_ml export ..., we will move our other signing at a later date.
- Swapped how credentials are obtained for ROLE iam credentials provider such that it uses a botocore session now instead of calling the ec2 metadata service. This should make the module more usable outside of Sagemaker.
- Added sub-configuration for sparql to allow specifying path to sparql endpoint

#### New Line magics:

- `%neptune_ml export status`
- `%neptune_ml dataprocessing start`
- `%neptune_ml dataprocessing status`
- `%neptune_ml training start`
- `%neptune_ml training status`
- `%neptune_ml endpoint create`
- `%neptune_ml endpoint status`

#### New Cell magics:

- `%%neptune_ml export start`
- `%%neptune_ml dataprocessing start`
- `%%neptune_ml training start`
- `%%neptune_ml endpoint create`
NOTE: If a cell magic is used, its line inputs for specifying parts of the command will be ignore such as `--job-id` as a line-param.

Inject variable as cell input:
Currently this will only work for our new cell magic commands details above. You can now specify a variable to use as the cell input received by our `neptune_ml` magics using the syntax ${var_name}. For example...

```
# in one notebook cell:
foo = {'foo', 'bar'}

# in another notebook cell:
%%neptune_ml export start

${foo}
```

NOTE: The above will only work if it is the sole content of the cell body. You cannot inline multiple variables at this time.

#### SPARQL Enhancements
- Support to allow namespace specification for Blazegraph endpoints by specify the prefix to the sparql endpoint being queried.
- Add new config section for sparql-specific items [Link to PR](https://github.com/aws/graph-notebook/pull/49)
- Specify explain prefix_path param explicitly in `%%sparql explain` magic variant [Link to PR](https://github.com/aws/graph-notebook/pull/52)

## Release 2.0.1 (Nov 23, 2020)

- Fixed bug in argparser for load_status and cancel_load line magics [Link to PR](https://github.com/aws/graph-notebook/pull/37)
- Expanded loader status values that terminate load line magic

## Release 2.0.0 (Nov 20, 2020)

- Added support for storing query results to a variable for use in other notebook cells [Link to PR](https://github.com/aws/graph-notebook/pull/18)
- Removed %query_mode magic in favor of query parameterization [Link to PR](https://github.com/aws/graph-notebook/pull/33)

## Release 1.33.0 (Nov 10, 2020)

- Fix compatibility with Windows by using path join instead of building paths using strings [Link to PR](https://github.com/aws/graph-notebook/pull/6)
- Added hooks to install nbextensions using the jupyter nbextension ... syntax
- Fix issue preventing Gremlin results that contain a datetime object from being rendered properly

## Release 1.32.0 (Nov 4, 2020)

- Added a dependency revision for graph-notebook compatibility with Amazon Sagemaker. [Link to PR](https://github.com/aws/graph-notebook/pull/4)

See [here](https://github.com/aws/graph-notebook/tree/main/additional-databases/sagemaker) for a quick guide on launching graph-notebook using a SageMaker lifecycle configuration file.

## Release 1.31.6 (Nov 2, 2020)

First release of graph-notebook on GitHub and to [PyPI](https://pypi.org/project/graph-notebook/1.31.6/)

[Link to PR](https://github.com/aws/graph-notebook/pull/3)

The graph notebook is a Python library for Jupyter Notebooks that can run on local desktops and be used with databases that support either the RDF/SPARQL open standard or the open-source Apache TinkerPop graphs. 

See [here](https://github.com/aws/graph-notebook#features) for a list of major features.
