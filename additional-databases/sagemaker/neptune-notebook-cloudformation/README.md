## Launching graph-notebook as Amazon Neptune Workbench via AWS CloudFormation

The AWS CloudFormation template in this folder, [`neptune-workbench-stack.yaml`](neptune-workbench-stack.yaml), deploys Amazon Neptune workbench notebooks as resources, and includes the base 'Getting Started' notebooks. The workbench lets you work with your Amazon Neptune Database cluster using Jupyter notebooks hosted by Amazon SageMaker. You are billed for workbench resources through Amazon SageMaker, separately from your Neptune billing.

### Parameter details
#### Minimum permissions for the SageMakerNotebookRole
You may opt to have your notebook instance assume an existing AWS IAM role, via the `SageMakerNotebookRoleArn` stack parameter. Make sure that this role has at least the following minimum permissions within its service role policy:

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
        "arn:(AWS Partition):s3:::aws-neptune-notebook-(AWS Region)",
        "arn:(AWS Partition):s3:::aws-neptune-notebook-(AWS Region)/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "neptune-db:connect",
      "Resource": [
        "arn:(AWS Partition):neptune-db:(AWS Region):(AWS Account ID):(Cluster Resource ID)/*"
      ]
    }
  ]
}
```

If you would like to enable CloudWatch logging, also add:
```json
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:(AWS Partition):logs:(AWS Region):(AWS Account ID):log-group:/aws/sagemaker/*"
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
