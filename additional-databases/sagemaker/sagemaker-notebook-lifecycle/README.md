## Launching graph-notebook on Amazon SageMaker using a lifecycle
You can easily configure graph-notebook to run on an Amazon SageMaker Notebook instance by using a lifecycle configuration. To learn more about lifecycle configurations and how to create one, see [documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html).

Use the sample lifecycle configuration in this folder, [`install-graph-notebook-lc.sh`](install-graph-notebook-lc.sh) ([`install-graph-notebook-lc-cn.sh`](install-graph-notebook-lc-cn.sh) if using `cn-north-1` or `cn-northwest-1` region) or create your own shell script. 

After you create a lifecycle configuration on SageMaker, you can create new notebook instances by specifying a saved lifecycle configuration:

![create-a-notebook](/images/Create-Notebook-Instance.png)
