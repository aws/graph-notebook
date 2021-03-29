# graph-notebook Change Log

Starting with v1.31.6, this file will contain a record of major features and updates made in each release of graph-notebook.

## Upcoming

- Add support for Mode, queueRequest, and Dependencies parameters when running %load command

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
