# graph-notebook Change Log

Starting with v1.31.6, this file will contain a record of major features and updates made in each release of graph-notebook.

## Upcoming

## Release 5.0.0 (April 8, 2025)
- Upgrade project to Jupyterlab 4x ([Link to PR](https://github.com/aws/graph-notebook/pull/729))
- 
## Release 4.6.2 (November 26, 2024)
- Added Neptune `--use-port` option to `%%gremlin` and `%%oc` ([Link to PR](https://github.com/aws/graph-notebook/pull/712))
- Fixed SPARQL path in example Fuseki configuration ([Link to PR](https://github.com/aws/graph-notebook/pull/713))
- Mitigated visualizer crash on newer `jupyterlab-widgets` versions ([Link to PR](https://github.com/aws/graph-notebook/pull/716))
- Fixed TS errors in visualizer widget build ([Link to PR](https://github.com/aws/graph-notebook/pull/716))

## Release 4.6.1 (October 1, 2024)

- Updated `%%oc` to use the `/queries` endpoint for Neptune Analytics ([Link to PR](https://github.com/aws/graph-notebook/pull/705))
- Added experimental TinkerPop 4.0 support ([Link to PR](https://github.com/aws/graph-notebook/pull/704))
- Added documentation for group keys in `%%graph_notebook_vis_options` ([Link to PR](https://github.com/aws/graph-notebook/pull/703))
- Enabled `--query-timeout` on `%%oc explain` for Neptune Analytics ([Link to PR](https://github.com/aws/graph-notebook/pull/701))

## Release 4.6.0 (September 19, 2024)

- Updated Gremlin config `message_serializer` to accept all TinkerPop serializers ([Link to PR](https://github.com/aws/graph-notebook/pull/685))
- Implemented service-based dynamic allowlists and defaults for Gremlin serializer and protocol combinations ([Link to PR](https://github.com/aws/graph-notebook/pull/697))
- Added `%get_import_task` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/668))
- Added `--export-to` JSON file option to `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/684))
- Deprecated Python 3.8 support ([Link to PR](https://github.com/aws/graph-notebook/pull/683))
- Upgraded Neo4j Bolt driver to v5.x ([Link to PR](https://github.com/aws/graph-notebook/pull/682))
- Upgraded nest_asyncio to 1.6.0 ([Link to PR](https://github.com/aws/graph-notebook/pull/698))
- Improved iPython config directory retrieval logic ([Link to PR](https://github.com/aws/graph-notebook/pull/687))
- Fixed `%db_reset` output for token modes ([Link to PR](https://github.com/aws/graph-notebook/pull/691))
- Fixed `%%gremlin profile` serialization issue on Neptune DB v1.2 and older ([Link to PR](https://github.com/aws/graph-notebook/pull/694))
- Use `extras_require` to specify tests ([Link to PR](https://github.com/aws/graph-notebook/pull/688))
- Updated Gremlin HTTP requests, fixed handling of internal error responses ([Link to PR](https://github.com/aws/graph-notebook/pull/692))

## Release 4.5.2 (August 15, 2024)

- New Neptune Analytics notebooks - openCypher over RDF ([Link to PR](https://github.com/aws/graph-notebook/pull/672))
  - Path: 02-Neptune-Analytics > 04-OpenCypher-Over-RDF
- Updated OC-RDF samples to use `%load` magic, and pull from regional S3 buckets ([Link to PR](https://github.com/aws/graph-notebook/pull/676))
- Added regional S3 bucket mappings to Neptune CloudFormation template ([Link to PR](https://github.com/aws/graph-notebook/pull/664))
- Enabled n-triples data for `%load` with Neptune Analytics ([PR #1](https://github.com/aws/graph-notebook/pull/671)) ([PR #2](https://github.com/aws/graph-notebook/pull/675))
- Removed unused options from `%load`([Link to PR](https://github.com/aws/graph-notebook/pull/662))
- Made EncryptionKey optional in Neptune CloudFormation template ([Link to PR](https://github.com/aws/graph-notebook/pull/663))
- Fixed unintended type coercion in results table with missing/null values ([Link to PR](https://github.com/aws/graph-notebook/pull/679))

## Release 4.5.1 (July 31, 2024)

- Added `%create_graph_snapshot` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/653))
- Added better `%reset` user messaging on status check timeout ([Link to PR](https://github.com/aws/graph-notebook/pull/652))
- Modified the `%reset --snapshot` option to use the CreateGraphSnapshot API ([Link to PR](https://github.com/aws/graph-notebook/pull/654))
- Upgraded `pandas` dependency to 2.x ([Link to PR](https://github.com/aws/graph-notebook/pull/658))
- Upgraded `setuptools` dependency to 70.x ([Link to PR](https://github.com/aws/graph-notebook/pull/649))
- Experimental support for Python 3.11 ([PR #1](https://github.com/aws/graph-notebook/pull/645)) ([PR #2](https://github.com/aws/graph-notebook/pull/656))
- Updated sample SageMaker Lifecycle scripts ([Link to PR](https://github.com/aws/graph-notebook/pull/657))

## Release 4.5.0 (July 15, 2024)

- New Neptune Database notebook - Games Industry Graphs ([Link to PR](https://github.com/aws/graph-notebook/pull/566))
  - Path: 01-Neptune-Database > 03-Sample-Applications > 07-Games-Industry-Graphs
- Added unified `%reset` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/644))
- Added `--connected-table` option to magics with table widget output ([Link to PR](https://github.com/aws/graph-notebook/pull/634))
- Added `--silent` option to the `%%graph_notebook_config` line and cell magics ([Link to PR](https://github.com/aws/graph-notebook/pull/641))
- Added helpful redirect messaging for service-specific Neptune magics ([Link to PR](https://github.com/aws/graph-notebook/pull/643))
- Changed `%%gremlin --store-to` to also store exceptions from non-Neptune queries ([Link to PR](https://github.com/aws/graph-notebook/pull/635))
- Fixed broken `--help` option for `%%gremlin` ([Link to PR](https://github.com/aws/graph-notebook/pull/630))
- Fixed openCypher query bug regression in the [`01-About-the-Neptune-Notebook`](https://github.com/aws/graph-notebook/blob/main/src/graph_notebook/notebooks/01-Getting-Started/01-About-the-Neptune-Notebook.ipynb) sample ([Link to PR](https://github.com/aws/graph-notebook/pull/631))
- Fixed `%%graph_notebook_config` error when excluding optional Gremlin section ([Link to PR](https://github.com/aws/graph-notebook/pull/633))
- Fixed `--mode` argument for Neptune DB bulk loader requests via `%load` ([Link to PR](https://github.com/aws/graph-notebook/pull/637))
- Switched to generating Jinja2 templates in sandboxed environment ([Link to PR](https://github.com/aws/graph-notebook/pull/639))
- Removed unnecessarily verbose output from `get_config` function ([Link to PR](https://github.com/aws/graph-notebook/pull/642))

## Release 4.4.2 (June 18, 2024)

- Set Gremlin `connection_protocol` defaults based on Neptune service when generating configuration via arguments ([Link to PR](https://github.com/aws/graph-notebook/pull/626))

## Release 4.4.1 (June 17, 2024)

- Added `--connection-protocol` option to `%%gremlin` ([Link to PR](https://github.com/aws/graph-notebook/pull/617))
- Added global Gremlin `connection_protocol` setting to `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/621))
- Added various enhancements for `%%gremlin` HTTP connections to Neptune ([Link to PR](https://github.com/aws/graph-notebook/pull/624))
- Restored left alignment of numeric value columns in results table widget ([Link to PR](https://github.com/aws/graph-notebook/pull/620))

## Release 4.4.0 (June 10, 2024)

- Added `%reset_graph` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/610))
- Added `%get_graph` line magic, support `%status` for Neptune Analytics ([Link to PR](https://github.com/aws/graph-notebook/pull/611))
- Added `%%oc --plan-cache` support for Neptune DB ([Link to PR](https://github.com/aws/graph-notebook/pull/613))
- Upgraded to Gremlin-Python 3.7 ([Link to PR](https://github.com/aws/graph-notebook/pull/597))

## Release 4.3.1 (June 3, 2024)

- New notebooks showing Telco examples leveraging GNN and LLM ([Link to PR](https://github.com/aws/graph-notebook/pull/587))
  - Path: 03-Neptune-ML > 03-Sample-Applications > 04-Telco-Networks
- Added KMS encryption support to NeptuneDB Notebook CloudFormation template ([Link to PR](https://github.com/aws/graph-notebook/pull/590))
- Added warnings for usage of `%%oc` with incompatible Neptune Analytics parameters ([Link to PR](https://github.com/aws/graph-notebook/pull/599))
- Added download and copy buttons to results table widgets ([Link to PR](https://github.com/aws/graph-notebook/pull/602))
- Improved handling of mixed type Gremlin results ([Link to PR](https://github.com/aws/graph-notebook/pull/592))
- Upgraded `rdflib` to 7.0.0 and `SPARQLWrapper` to 2.0.0 ([Link to PR](https://github.com/aws/graph-notebook/pull/596))
- Upgraded `requests` to 2.32.x ([Link to PR](https://github.com/aws/graph-notebook/pull/600))
- Upgraded `itables` to 2.x ([Link to PR](https://github.com/aws/graph-notebook/pull/601))
- Fixed formatting of query magic `--help` entries listing valid inputs ([Link to PR](https://github.com/aws/graph-notebook/pull/593))
- Fixed endpoint creation bug in People-Analytics-using-Neptune-ML sample ([Link to PR](https://github.com/aws/graph-notebook/pull/595))
- Fixed deprecated usage of Pandas `DataFrameGroupBy.mean` in NeptuneML SPARQL utils ([Link to PR](https://github.com/aws/graph-notebook/pull/596))
- Updated default %graph_notebook_config to display Neptune-specific fields ([Link to PR](https://github.com/aws/graph-notebook/pull/605))

## Release 4.2.0 (April 4, 2024)

- New Neptune Analytics notebooks - SBOM ([Link to PR](https://github.com/aws/graph-notebook/pull/566))
  - Path: 02-Neptune-Analytics > 03-Sample-Use-Cases > 03-Software-Bill-Of-Materials
- Added `--store-format` option to query magics ([Link to PR](https://github.com/aws/graph-notebook/pull/580))
- Added `--export-to` CSV file option to query magics ([Link to PR](https://github.com/aws/graph-notebook/pull/582))
- Added `%graph_pg_info` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/570))
- Added `@neptune_graph_only` magics decorator ([Link to PR](https://github.com/aws/graph-notebook/pull/569))
- Added documentation for FontAwesome 5 settings ([Link to PR](https://github.com/aws/graph-notebook/pull/575))
- Updated `create-graph` CLI commands in Neptune Analytics samples ([Link to PR](https://github.com/aws/graph-notebook/pull/565))
- Updated NeptuneDB Notebook CloudFormation template ([Link to PR](https://github.com/aws/graph-notebook/pull/571))
- Fixed unintended formatting in `%%oc explain` widget ([Link to PR](https://github.com/aws/graph-notebook/pull/576))
- Fixed serialization of NoneType for `%%oc` query parameters ([Link to PR](https://github.com/aws/graph-notebook/pull/584))
- Changed `%load` parameter and default value for failOnError ([Link to PR](https://github.com/aws/graph-notebook/pull/577))

## Release 4.1.0 (February 1, 2024)

- New Neptune Analytics notebook - Vector Similarity Algorithms ([Link to PR](https://github.com/aws/graph-notebook/pull/555))
  - Path: 02-Neptune-Analytics > 02-Graph-Algorithms > 06-Vector-Similarity-Algorithms
- Updated various Neptune magics for new Analytics API ([Link to PR](https://github.com/aws/graph-notebook/pull/560))
- Added `%graph_notebook_service` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/560))
- Added unit abbreviation support to `--max-content-length` ([Link to PR](https://github.com/aws/graph-notebook/pull/553))
- Deprecated Python 3.7 support ([Link to PR](https://github.com/aws/graph-notebook/pull/551))

## Release 4.0.2 (Dec 14, 2023)

- Fixed `neptune_ml_utils` imports in `03-Neptune-ML` samples ([Link to PR](https://github.com/aws/graph-notebook/pull/546))
- Enable Gremlin `message_serializer` config field for Neptune endpoints ([Link to PR](https://github.com/aws/graph-notebook/pull/547))

## Release 4.0.1 (Nov 29, 2023)

- Fixed @neptune_db_only magics decorator ([Link to PR](https://github.com/aws/graph-notebook/pull/543))

## Release 4.0.0 (Nov 29, 2023)

- Added support for Neptune Analytics ([Link to PR](https://github.com/aws/graph-notebook/pull/541))
- Added Air-Routes and EPL sample seed datasets for openCypher ([Link to PR](https://github.com/aws/graph-notebook/pull/540))

## Release 3.9.0 (Oct 9, 2023)

- New Gremlin Language Tutorial notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/533))
  - Path: 06-Language-Tutorials > 03-Gremlin
- Added `--explain-type` option to `%%gremlin` ([Link to PR](https://github.com/aws/graph-notebook/pull/503))
- Added general documentation for `%%graph_notebook_config` options ([Link to PR](https://github.com/aws/graph-notebook/pull/504))
- Added support for Gremlin proxy hosts and visualization of Neptune HTTP results ([Link to PR](https://github.com/aws/graph-notebook/pull/530))
- Modified Dockerfile to support Python 3.10 ([Link to PR](https://github.com/aws/graph-notebook/pull/519))
- Updated Docker documentation with platform-specific run commands ([Link to PR](https://github.com/aws/graph-notebook/pull/502))
- Fixed deprecation warnings in GitHub workflows ([Link to PR](https://github.com/aws/graph-notebook/pull/506))
- Fixed seed dataset unzip path in Identity Graph sample notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/507))
- Fixed unit test workflows failing on type check assertion ([Link to PR](https://github.com/aws/graph-notebook/pull/514))
- Fixed bad queries in openCypher Language Tutorial samples ([PR #1](https://github.com/aws/graph-notebook/pull/525)) ([PR #2](https://github.com/aws/graph-notebook/pull/526))
- Fixed kernel crashing with ZMQ errors on magic execution ([Link to PR](https://github.com/aws/graph-notebook/pull/517))
- Fixed truncated descriptions for some `%seed` fields ([Link to PR](https://github.com/aws/graph-notebook/pull/531))
- Unpinned `boto3` and `botocore` to support NeptuneData SDK ([Link to PR](https://github.com/aws/graph-notebook/pull/528))

## Release 3.8.2 (June 5, 2023)

- New Sample Applications - Healthcare and Life Sciences notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/484))
  - Path: 03-Sample-Applications > 05-Healthcare-and-Life-Sciences-Graphs
- Added local file path and openCypher query support to `%seed` ([Link to PR](https://github.com/aws/graph-notebook/pull/292))
- Added S3 path support to `%seed` ([Link to PR](https://github.com/aws/graph-notebook/pull/488))
- Added samples options for openCypher to `%seed` ([Link to PR](https://github.com/aws/graph-notebook/pull/494))
- Added support for openCypher parameterized queries ([Link to PR](https://github.com/aws/graph-notebook/pull/496))
- Added `%toggle_traceback` line magic ([Link to PR](https://github.com/aws/graph-notebook/pull/486))
- Added support for setting `%graph_notebook_vis_options` from a variable ([Link to PR](https://github.com/aws/graph-notebook/pull/487))
- Pinned JupyterLab<4.x to fix Python 3.8/3.10 builds ([Link to PR](https://github.com/aws/graph-notebook/pull/490))
- Changed datatype of "amount" from String to numeric for "Transaction" vertices in Fraud Graph sample notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/489))
- Replaced usages of deprecated DataFrame.append method in ML samples ([Link to PR](https://github.com/aws/graph-notebook/pull/495))
- Set Gremlin as default language for PropertyGraph samples in `%seed` ([Link to PR](https://github.com/aws/graph-notebook/pull/497))
- Suppress InsecureRequestWarning if SSL verification is disabled ([Link to PR](https://github.com/aws/graph-notebook/pull/499))

## Release 3.8.1 (April 17, 2023)

- Reinstate Python 3.7 support for compatibility with legacy AL1 Neptune Notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/479))

## Release 3.8.0 (April 16, 2023)

- Added support for Python 3.10 ([Link to PR](https://github.com/aws/graph-notebook/pull/476))
- Deprecated Python 3.7 support ([PR #1](https://github.com/aws/graph-notebook/pull/453)) ([PR #2](https://github.com/aws/graph-notebook/pull/473))
- Patched nbextensions loader timeouts for large notebooks ([PR #1](https://github.com/aws/graph-notebook/pull/455))
- Fixed Dockerfile builds breaking with AL2023 ([Link to PR](https://github.com/aws/graph-notebook/pull/466))
- Fixed `--store-to` option for several magics ([Link to PR](https://github.com/aws/graph-notebook/pull/463))
- Fixed broken documentation links in Neptune ML notebooks ([PR #1](https://github.com/aws/graph-notebook/pull/467)) ([PR #2](https://github.com/aws/graph-notebook/pull/468))
- Fixed Gremlin graph tab not rendering with UUID type IDs ([Link to PR](https://github.com/aws/graph-notebook/pull/475))

## Release 3.7.3 (March 14, 2023)

- Fixed detailed mode output for graph summary requests ([Link to PR](https://github.com/aws/graph-notebook/pull/461))
- Added more helpful error messaging for `%statistics`/`%summary` ([Link to PR](https://github.com/aws/graph-notebook/pull/460))
- Added Neptune Notebook CloudFormation template ([Link to PR](https://github.com/aws/graph-notebook/pull/442))

## Release 3.7.2 (March 9, 2023)

- New Neptune ML notebook - Real Time Fraud Detection using Inductive Inference ([Link to PR](https://github.com/aws/graph-notebook/pull/338))
  - Path: 04-Machine-Learning > Sample-Applications > 03-Real-Time-Fraud-Detection-Using-Inductive-Inference.ipynb
- New openCypher Language Tutorial notebooks
  - Path: 06-Language-Tutorials > 02-openCypher
- Added support for Neptune Summary API ([Link to PR](https://github.com/aws/graph-notebook/pull/457))
- Added `--profile-misc-args` option to `%%gremlin` ([Link to PR](https://github.com/aws/graph-notebook/pull/443))
- Added error messaging for incompatible host-specific `%%graph_notebok_config` parameters ([Link to PR](https://github.com/aws/graph-notebook/pull/456))
- Ensure default assignments for all Gremlin nodes when using grouping ([Link to PR](https://github.com/aws/graph-notebook/pull/448))
- Fixed nbextensions loader timeout on large notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/455))

## Release 3.7.1 (January 25, 2023)

- Added ECR auto-publish workflow ([Link to PR](https://github.com/aws/graph-notebook/pull/405))
- Added support for list/tuple element access in cell variable injection ([Link to PR](https://github.com/aws/graph-notebook/pull/409))
- Fixed failing endpoint creation step in [01-People-Analytics/People-Analytics-using-Neptune-ML](https://github.com/aws/graph-notebook/blob/main/src/graph_notebook/notebooks/04-Machine-Learning/Sample-Applications/01-People-Analytics/People-Analytics-using-Neptune-ML.ipynb) ([Link to PR](https://github.com/aws/graph-notebook/pull/411))
- Fixed browser-specific issues with fullscreen graph widget ([Link to PR](https://github.com/aws/graph-notebook/pull/427))
- Fixed IAM authenticated Bolt queries failing on certain Neptune engine versions ([Link to PR](https://github.com/aws/graph-notebook/pull/438))
- Fixed query status magics failing with a TypeError ([Link to PR](https://github.com/aws/graph-notebook/pull/419))
- Pinned `numpy<1.24.0` to fix conflicts with `networkx` dependency during installation ([Link to PR](https://github.com/aws/graph-notebook/pull/416))
- Pinned version ceiling for all dependencies ([Link to PR](https://github.com/aws/graph-notebook/pull/431))
- Excluded certain `itables` versions causing errors in query magics ([PR #1](https://github.com/aws/graph-notebook/pull/429)) ([PR #2](https://github.com/aws/graph-notebook/pull/429))
- Truncated metadata request/query time metrics ([Link to PR](https://github.com/aws/graph-notebook/pull/425))
- Enabled unit test workflow runs for external pull requests ([Link to PR](https://github.com/aws/graph-notebook/pull/437))

## Release 3.7.0 (December 7, 2022)

- Added Neo4J section to `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/331))
- Added custom Gremlin authentication and serializer support ([Link to PR](https://github.com/aws/graph-notebook/pull/356))
- Added `%statistics` magic for Neptune DFE engine ([Link to PR](https://github.com/aws/graph-notebook/pull/377))
- Added option to disable TLS certificate verification in `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/372))
- Improved `%load` status output, fixed region option ([Link to PR](https://github.com/aws/graph-notebook/pull/395))
- Updated [`01-About-the-Neptune-Notebook`](https://github.com/aws/graph-notebook/blob/main/src/graph_notebook/notebooks/01-Getting-Started/01-About-the-Neptune-Notebook.ipynb) for openCypher ([Link to PR](https://github.com/aws/graph-notebook/pull/387))
- Fixed results not being displayed for SPARQL ASK queries ([Link to PR](https://github.com/aws/graph-notebook/pull/385))
- Fixed `%seed` failing to load SPARQL EPL dataset ([Link to PR](https://github.com/aws/graph-notebook/pull/389))
- Fixed `%db_reset` status output not displaying in JupyterLab ([Link to PR](https://github.com/aws/graph-notebook/pull/391))
- Fixed `%%gremlin` throwing error for result sets with multiple datatypes [Link to PR](https://github.com/aws/graph-notebook/pull/388))
- Fixed edge label creation in `02-Using-Gremlin-to-Access-the-Graph` ([Link to PR](https://github.com/aws/graph-notebook/pull/390))
- Fixed igraph command error in `02-Logistics-Analysis-using-a-Transportation-Network` ([Link to PR](https://github.com/aws/graph-notebook/pull/404))
- Bumped typescript to 4.1.x in graph_notebook_widgets ([Link to PR](https://github.com/aws/graph-notebook/pull/393))
- Pinned `ipywidgets==7.7.2` and `jupyterlab_widgets<3` ([Link to PR](https://github.com/aws/graph-notebook/pull/407))
- Pinned `nbclient<=0.7.0` ([Link to PR](https://github.com/aws/graph-notebook/pull/402))

## Release 3.6.2 (October 18, 2022)

- New Sample Applications - Security Graphs notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/373))
  - Path: 03-Sample-Applications > 04-Security-Graphs
- Update sample notebooks with parallel, same-direction edges example ([Link to PR](https://github.com/aws/graph-notebook/pull/366))
- Fixed a Gremlin widgets error caused by empty individual results ([Link to PR](https://github.com/aws/graph-notebook/pull/367))
- Fixed `%db_reset` timeout handling, made timeout limit configurable ([Link to PR](https://github.com/aws/graph-notebook/pull/369))
- Fixed Sparql visualizations occasionally failing with VisJS group assignment error ([Link to PR](https://github.com/aws/graph-notebook/pull/375))
- Fixed `start jupyterlab` command in README ([Link to PR](https://github.com/aws/graph-notebook/pull/376))
- Fixed interface rendering issue in classic notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/378))
- Added `--hide-index` option for query results ([Link to PR](https://github.com/aws/graph-notebook/pull/371))
- Added result media type selection for SPARQL queries ([Link to PR](https://github.com/aws/graph-notebook/pull/313))

## Release 3.6.0 (September 15, 2022)

- New Language Tutorials - SPARQL Basics notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/316))
  - Path: 06-Language-Tutorials > 01-SPARQL > 01-SPARQL-Basics
- New Neptune ML - Text Encoding Tutorial notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/338))
  - Path: 04-Machine-Learning > Sample-Applications > 02-Job-Recommendation-Text-Encoding.ipynb
- Added `--store-to` option to `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/347))
- Added loader status details options to `%load_ids` ([Link to PR](https://github.com/aws/graph-notebook/pull/354))
- Added `--all-in-queue` option to `%cancel_load` ([Link to PR](https://github.com/aws/graph-notebook/pull/355))
- Deprecated Python 3.6 support ([Link to PR](https://github.com/aws/graph-notebook/pull/353))
- Added support for literal property values in Sparql visualization options ([Link to PR](https://github.com/aws/graph-notebook/pull/296))
- Various results table improvements ([Link to PR](https://github.com/aws/graph-notebook/pull/349))
- Disabled automatic collapsing of large explain results ([Link to PR](https://github.com/aws/graph-notebook/pull/363))
- Fixed version-specific steps in SageMaker installation script ([Link to PR](https://github.com/aws/graph-notebook/pull/359))
- Added new SageMaker installation script for China regions ([Link to PR](https://github.com/aws/graph-notebook/pull/361))

## Release 3.5.3 (July 25, 2022)

- Docker support. Docker image can be built using the command `docker build .` and through Docker's `buildx`, this can support non-x86 CPU Architectures like ARM. ([Link to PR](https://github.com/aws/graph-notebook/pull/323))
  - Fix `service.sh` conditional checks, SSL parameter can now be changed. Fix permissions error on `service.sh` experienced by some users. ([Link to PR](https://github.com/aws/graph-notebook/pull/335))
- Added `%%neptune_config_allowlist` magic ([Link to PR](https://github.com/aws/graph-notebook/pull/327))
- Added check to remove whitespace in `%graph_notebook_config` host fields ([Link to PR](https://github.com/aws/graph-notebook/pull/329))
- Added silent output option to additional magics ([Link to PR](https://github.com/aws/graph-notebook/pull/326))
- Fixed %sparql_status magic to return query status without query ID ([Link to PR](https://github.com/aws/graph-notebook/pull/337))
- Fixed incorrect Gremlin query --store-to output ([Link to PR](https://github.com/aws/graph-notebook/pull/334))
- Fixed certain characters not displaying correctly in results table ([Link to PR](https://github.com/aws/graph-notebook/pull/341))
- Fixed extra index column displaying in Gremlin results table on older Pandas versions ([Link to PR](https://github.com/aws/graph-notebook/pull/343))
- Reverted Gremlin console tab to single results column ([Link to PR](https://github.com/aws/graph-notebook/pull/330))
- Bumped jquery-ui from 1.13.1 to 1.13.2 (([Link to PR](https://github.com/aws/graph-notebook/pull/328))

## Release 3.5.1 (July 12, 2022)

- Improved the `%stream_viewer` magic to show the commit timestamp and `isLastOp` information,
  if available. Also added additional hover (help) text to the stream viewer. ([Link to PR](https://github.com/aws/graph-notebook/pull/311))
- Added `--max-content-length` option to `%%gremlin` ([Link to PR](https://github.com/aws/graph-notebook/pull/305))
- Added `proxy_host` and `proxy_port` options to the `%%graph_notebook_config` options. ([Link to PR](https://github.com/aws/graph-notebook/pull/310))
  - This allows for proxied connections to your Neptune instance from outside your VPC. Supporting the patterns seen [here](https://aws-samples.github.io/aws-dbs-refarch-graph/src/connecting-using-a-load-balancer/).
- Fixed results table formatting in JupyterLab ([Link to PR](https://github.com/aws/graph-notebook/pull/297))
- Fixed several typos in the Neptune ML 00 notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/319))
- Renamed the Knowledge Graph application notebooks for clarity ([Link to PR](https://github.com/aws/graph-notebook/pull/320))

## Release 3.4.1 (June 7, 2022)

- Identity Graph - ETL notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/288))
  - Path: 03-Identity-Graphs>03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL
  - Files: scripts/, glue_utils.py and 3-Identity-Graphs>03-Jumpstart-Identity-Graphs-Using-Canonical-Model-and-ETL notebook
- Support variable injection in `%%graph_notebook_config` magic ([Link to PR](https://github.com/aws/graph-notebook/pull/287))
- Added three notebooks to show data science workflows with Amazon Neptune ([Link to PR](https://github.com/aws/graph-notebook/pull/302))
- Added JupyterLab startup script to auto-load magics extensions ([Link to PR](https://github.com/aws/graph-notebook/pull/277))
- Added includeWaiting option to %oc_status, fix same for %gremlin_status ([Link to PR](https://github.com/aws/graph-notebook/pull/272))
- Added `--store-to` option to %status ([Link to PR](https://github.com/aws/graph-notebook/pull/278))
- Fixed handling of empty nodes returned from openCypher `DELETE` queries ([Link to PR](https://github.com/aws/graph-notebook/pull/286))
- Fixed rendering of openCypher widgets for empty result sets ([Link to PR](https://github.com/aws/graph-notebook/pull/286))
- Fixed graph search overriding physics setting ([Link to PR](https://github.com/aws/graph-notebook/pull/282))
- Fixed browser-specific bug in results pagination options menu ([Link to PR](https://github.com/aws/graph-notebook/pull/290))
- Fixed invalid queries in Gremlin sample notebooks ([Link to PR](https://github.com/aws/graph-notebook/pull/308))
- Removed `requests-aws4auth` requirement ([Link to PR](https://github.com/aws/graph-notebook/pull/291))

## Release 3.3.0 (March 28, 2022)

- Support rendering of widgets in JupyterLab ([Link to PR](https://github.com/aws/graph-notebook/pull/271))
- Fixed ASCII encoding error in Profile/Explain generation ([Link to PR](https://github.com/aws/graph-notebook/pull/275))
- Fixed inaccessible data URL in NeptuneML utils ([Link to PR](https://github.com/aws/graph-notebook/pull/279))
- Fixed integration tests to address updated air routes data and other changes ([Link to PR](https://github.com/aws/graph-notebook/pull/270))
- Bumped jinja2 from 2.10.1 to 3.0.3 ([Link to PR](https://github.com/aws/graph-notebook/pull/283))
- Added documentation for JupyterLab installation ([Link to PR](https://github.com/aws/graph-notebook/pull/284))

## Release 3.2.0 (February 25, 2022)

- Added new notebooks: guides for using SPARQL and RDF with Neptune ML ([Link to PR](https://github.com/aws/graph-notebook/pull/252))
- Added the ability to run explain plans to openCypher queries via `%%oc explain`. ([Link to PR](https://github.com/aws/graph-notebook/pull/265))
- Added the ability to download the explain/profile plans for openCypher/Gremlin/SPARQL. ([Link to PR](https://github.com/aws/graph-notebook/pull/265))
- Changed the `%stream_viewer` magic to use `PropertyGraph` and `RDF` as the stream types. This better aligns with Gremlin and openCypher sharing the `PropertyGraph` stream. ([Link to PR](https://github.com/aws/graph-notebook/pull/261))
- Updated the airports property graph seed files to the latest level and suffixed all doubles with 'd'. ([Link to PR](https://github.com/aws/graph-notebook/pull/257))
- Added grouping by depth for Gremlin and openCypher queries ([PR #1](https://github.com/aws/graph-notebook/pull/241))([PR #2](https://github.com/aws/graph-notebook/pull/251))
- Added grouping by raw node results ([Link to PR](https://github.com/aws/graph-notebook/pull/253))
- Added loading from file path with `%seed` ([Link to PR](https://github.com/aws/graph-notebook/pull/247))
- Added `--no-scroll` option for disabling truncation of query result pages ([Link to PR](https://github.com/aws/graph-notebook/pull/243))
- Added `--results-per-page` option ([Link to PR](https://github.com/aws/graph-notebook/pull/242))
- Added relaxed seed command error handling ([Link to PR](https://github.com/aws/graph-notebook/pull/246))
- Renamed Gremlin profile query options for clarity ([Link to PR](https://github.com/aws/graph-notebook/pull/249))
- Suppressed default root logger error output ([Link to PR](https://github.com/aws/graph-notebook/pull/248))
- Fixed Gremlin visualizer bug with handling non-string node IDs ([Link to PR](https://github.com/aws/graph-notebook/pull/245))
- Fixed error in openCypher Bolt query metadata output ([Link to PR](https://github.com/aws/graph-notebook/pull/255))
- Fixed handling of Decimal type properties when rendering Gremlin query results ([Link to PR](https://github.com/aws/graph-notebook/pull/256))

## Release 3.1.1 (December 21, 2021)

- Added new dataset for DiningByFriends, and associated notebook ([Link to PR](https://github.com/aws/graph-notebook/pull/235))
- Added new Neptune ML Sample Application for People Analytics ([Link to PR](https://github.com/aws/graph-notebook/pull/235))
- Added graph customization support for SPARQL queries ([Link to PR](https://github.com/aws/graph-notebook/pull/236))
- Added graph reset and search refinement buttons to the graph output tab ([Link to PR](https://github.com/aws/graph-notebook/pull/238))
- Added support for setting custom edge and node tooltips ([Link to PR](https://github.com/aws/graph-notebook/pull/227))
- Added edge tooltips, and options for specifying edge label length ([Link to PR](https://github.com/aws/graph-notebook/pull/218))
- Updated NeptuneML pre-trained model resources for CN regions ([Link to PR](https://github.com/aws/graph-notebook/pull/226))
- Fixed inaccurate help message being displayed for certain GremlinServerErrors ([Link to PR](https://github.com/aws/graph-notebook/pull/230))
- Fixed error causing query autocompletion to fail ([Link to PR](https://github.com/aws/graph-notebook/pull/231))
- Fixed Jupyter start script for cases where the nbconfig directory is missing ([Link to PR](https://github.com/aws/graph-notebook/pull/239))

## Release 3.0.8 (November 3, 2021)

- Added support for specifying the Gremlin traversal source ([Link to PR](https://github.com/aws/graph-notebook/pull/221))
- Added edge tooltips, and options for specifying edge label length ([Link to PR](https://github.com/aws/graph-notebook/pull/218))
- Fixed configuration options missing when using a CN region Neptune host ([Link to PR](https://github.com/aws/graph-notebook/pull/223))
- Correct naming of ID parameter for NeptuneML Endpoint command ([Link to PR](https://github.com/aws/graph-notebook/pull/217))

## Release 3.0.7 (October 25, 2021)

- Added full support for NeptuneML API command parameters to `%neptune_ml` ([Link to PR](https://github.com/aws/graph-notebook/pull/202))
- Allow `%%neptune_ml` to accept JSON blob as parameter input for most phases ([Link to PR](https://github.com/aws/graph-notebook/pull/202))
- Added `--silent` option for suppressing query output ([PR #1](https://github.com/aws/graph-notebook/pull/201)) ([PR #2](https://github.com/aws/graph-notebook/pull/203))
- Added all `parserConfiguration` options to `%load` ([Link to PR](https://github.com/aws/graph-notebook/pull/205))
- Upgraded to Gremlin-Python 3.5 and Jupyter Notebook 6.x ([Link to PR](https://github.com/aws/graph-notebook/pull/209))
- Resolved smart indent bug in openCypher magic cells ([Link to PR](https://github.com/aws/graph-notebook/pull/209))
- Removed default `/sparql` path suffix from non-Neptune SPARQL requests ([Link to PR](https://github.com/aws/graph-notebook/pull/210))

## Release 3.0.6 (September 20, 2021)

- Added a new `%stream_viewer` magic that allows interactive exploration of the Neptune CDC stream (if enabled). ([Link to PR](https://github.com/aws/graph-notebook/pull/191))
- Added support for multi-property values in vertex and edge labels ([Link to PR](https://github.com/aws/graph-notebook/pull/186))
- Added new visualization physics options, toggle button ([Link to PR](https://github.com/aws/graph-notebook/pull/190))
- Fixed TypeError thrown for certain OC list type results ([Link to PR](https://github.com/aws/graph-notebook/pull/196)
- Documentation fixes for additional databases ([Link to PR](https://github.com/aws/graph-notebook/pull/198))

## Release 3.0.5 (August 27, 2021)

- Disabled SigV4 signing for non-IAM AWS requests ([Link to PR](https://github.com/aws/graph-notebook/pull/179))
- Added new `--nopoll` option to `%load` to disable status polling ([Link to PR](https://github.com/aws/graph-notebook/pull/180))
- Made Neptune specific parameters optional for `%%graph_notebook_config` ([Link to PR](https://github.com/aws/graph-notebook/pull/181))
- Upgraded Jupyter Notebook dependency to 5.7.13 for security fix ([Link to PR](https://github.com/aws/graph-notebook/pull/182))
- Improved usability of %load Edge IDs option ([Link to PR](https://github.com/aws/graph-notebook/pull/183))

## Release 3.0.3 (August 11, 2021)

- Gremlin visualization bugfixes ([PR #1](https://github.com/aws/graph-notebook/pull/166)) ([PR #2](https://github.com/aws/graph-notebook/pull/174)) ([PR #3](https://github.com/aws/graph-notebook/pull/175))
- Updated the airport data loadable via %seed to the latest version ([Link to PR](https://github.com/aws/graph-notebook/pull/172))
- Added support for Gremlin Profile API parameters ([Link to PR](https://github.com/aws/graph-notebook/pull/171))
- Improved %seed so that the progress bar is seen to complete ([Link to PR](https://github.com/aws/graph-notebook/pull/173))
- Added helper functions to neptune_ml utils to get node embeddings, model predictions and performance metrics ([Link to PR](https://github.com/aws/graph-notebook/pull/170))
- Changed visualization behavior to add all group-less nodes to a default group ([Link to PR](https://github.com/aws/graph-notebook/pull/175))
- Fixed a bug causing ML Export requests to fail ([Link to PR](https://github.com/aws/graph-notebook/pull/178))

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

- Added "What’s Next" sections to 01-Getting-Started notebooks to suggest users to relevant notebook tutorials [Link to PR](https://github.com/aws/graph-notebook/pull/60)

## Release 2.0.6 (Jan 28, 2021)

- Added missing **init** to notebook directories to they get installed correctly
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
