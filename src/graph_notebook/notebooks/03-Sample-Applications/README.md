# Sample Applications Overview

- [Fraud Graph](#Fraud-Graph)
- [Knowledge Graph](#Knowledge-Graph)
- [Identity Graph](#Identity-Graph)
- [Security Graph](#Security-Graph)
- [Healthcare and Life Sciences Graphs](#Healthcare-and-Life-Sciences-Graphs)
- [Neptune ML - People Analytics](#Neptune-ML-People-Analytics)


## [Fraud Graph](./01-Fraud-Graphs/01-Building-a-Fraud-Graph-Application.ipynb)

Fraud hides itself in isolation. It exploits our failure to assess a transaction in the context of other recent transactions: patterns of fraudulent behaviour emerge only when we connect many seemingly discrete data points and events.

A fraud graph connects the entities participating in retail and financial transactions: entities such as accounts, transactions and merchants. By relating accounts and connecting transactions we improve our chances to detect and prevent fraud. With Amazon Neptune we can connect account and transaction information and query it whenever a new account or transaction is submitted to the system. Using queries that find patterns in our data that we know to be indicative of fraud, we can evaluate each transaction in the context of other transactions and accounts, and thereby determine whether constellations of data in the fraud graph represent fraudulent activity.

The examples in this notebook show how we can identify fraud rings (first-party fraud) and instances of identity theft (third-party fraud) in a credit card dataset.

## [Knowledge Graph](./02-Knowledge-Graphs/Building-a-Knowledge-Graph-Application-Gremlin.ipynb)

Modern knowledge graphs are the result of connections of data from multiple different sources. These sources can either be multiple different databases, different data silos, or data extracted from within entities stored in one or more of these options. Knowledge graphs come in many different forms but the unifying aspect of them is that they organize data using the entities and connections (known as semantics) familiar to a particular domain. It represents these semantics as definitions of concepts, their properties, relations between them, and the expected logical constraints. Logic built into such a model allows us to infer understanding and connections about the information contained within the model.

Knowledge graphs consolidate and integrate an organization’s information assets and make them more readily available to all members of the organization. There are many applications and use cases that are enabled by knowledge graphs. Information from disparate data sources can be linked and made accessible to answer questions you may not even have thought of yet. Information and entities can be extracted not only from structured sources (e.g., relational databases) but also from semi-structured sources (e.g., media, metadata, and spreadsheets) and unstructured sources (e.g., text documents, email, and news articles).

The examples in this notebook show how we can use our blog knowledge graph to demonstrate how we can use the connected nature of our knowledge graph to provide contextually relevant answers to search questions.

## [Identity Graph](./03-Identity-Graphs/01-Building-an-Identity-Graph-Application.ipynb)

An identity graph provides a single unified view of customers and prospects by linking multiple identifiers such as cookies, device identifiers, IP addresses, email IDs, and internal enterprise IDs to a known person or anonymous profile using privacy-compliant methods. Typically, identity graphs are part of a larger identity resolution architecture. Identity resolution is the process of matching human identity across a set of devices used by the same person or a household of persons for the purposes of building a representative identity, or known attributes, for targeted advertising.

The examples in this notebook shows a sample identity graph solution using an open dataset as well as data visualizations that allow one to better understand the structure of an identity graph.

## [Security Graph](./03-Security-Graphs/01-Building-a-Security-Graph-Application-with-Gremlin.ipynb)

A security graph connects resources within a network: entities such as policies, roles and resources. By relating these entities together we improve our chances to detect, prevent, and remediate security risk that violate compliance and enable better enforcement of security requirements. With Amazon Neptune we can connect entities together in such a way that we can query it whenever new resources are created in the system. Using queries that find patterns in our data that we know to be indicative of security risks, we can evaluate the scope and impact of these risks, and thereby determine whether constellations of data in the security graph represent a real or potential security issue.

The examples in this notebook shows a sample security graph solution using an open dataset as well as data visualizations that allow one to better understand the structure of a security graph.

## [Healthcare and Life Sciences Graphs](./05-Healthcare-and-Life-Sciences-Graphs/01-Modeling-Molecular-Structures-as-Graph-Data-Gremlin.ipynb)

A molecular modeling graph which represents chemical structures as graph data. Visualizing atoms as nodes, and the bonds between atoms as edges, enables users to explore chemical structures in a persistent environment. Using the popular open-source bioinformatics package RDKit, and a molecule represented as a SMILES string, walk through the process of transforming a molecule into a graph. Also, walk through a simple example of using packages in the graph-notebook environment.

The examples in this notebook show how to take the SMILES format string for the molecule caffeine and transform it into a graph representation. The notebook also includes exploration and visualization of the caffeine molecule as a graph.

## [People Analytics using Machine Learning](../04-Machine-Learning/Sample-Applications/01-People-Analytics)

Hiring and retaining good personnel is a key characteristic to making an organization successful.  One way that organizations approach this problem is through the use of people analytics.  People analytics allow business leaders to make data-driven decisions about personnel-related issues such as recruiting, evaluation, hiring, promotion, and retention, etc.

The examples in this notebook shows a sample people analytics graph solution using an open dataset that incorporates graph neural network based machine learning using Neptune ML.