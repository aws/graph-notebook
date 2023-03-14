## Launching graph-notebook as Amazon Neptune Workbench via AWS CloudFormation

The AWS CloudFormation template in this folder, [`neptune-workbench-stack.yaml`](neptune-workbench-stack.yaml), deploys Amazon Neptune workbench notebooks as resources, and includes the base 'Getting Started' notebooks. The workbench lets you work with your Amazon Neptune cluster using Jupyter notebooks hosted by Amazon SageMaker. You are billed for workbench resources through Amazon SageMaker, separately from your Neptune billing.

### Parameter details
#### Minimum permissions for the SageMakerNotebookRole
This is the ARN for the AWS IAM role that the notebook instance will assume. Make sure that this role has at least the following minimum permissions within its service role policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::aws-neptune-notebook",
        "arn:aws:s3:::aws-neptune-notebook/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "neptune-db:connect",
      "Resource": [
        "your-cluster-arn/*"
      ]
    }
  ]
}
```

The role should also establish the following trust relationship:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### How to populate the 'Cluster' value within the AWS Console for Amazon Neptune Notebooks
Add the following tags manually to the notebook instance.

| Key | Value |
| ------------- |-------------|
| **aws-neptune-cluster-id** | Amazon Neptune database cluster ID (found under *DB cluster id* under *Configuration* of the selected cluster in the AWS console) |
| **aws-neptune-resource-id** | Amazon Neptune cluster resource ID (found under *Resource id* under *Configuration* of the selected cluster in the AWS console) |
