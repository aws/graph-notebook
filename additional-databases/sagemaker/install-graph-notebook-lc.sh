#!/bin/bash

sudo -u ec2-user -i <<'EOF'

echo "export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT" >> ~/.bashrc  # set to IAM instead of DEFAULT if cluster is IAM enabled
echo "export GRAPH_NOTEBOOK_HOST=CHANGE-ME" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT=8182" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN=" >> ~/.bashrc
echo "export AWS_REGION=us-west-2" >> ~/.bashrc

source activate JupyterSystemEnv

echo "installing Python 3 kernel"
python3 -m ipykernel install --sys-prefix --name python3 --display-name "Python 3"

echo "installing python dependencies..."
pip uninstall NeptuneGraphNotebook -y # legacy uninstall when we used to install from source in s3

pip install --upgrade graph-notebook

echo "installing nbextensions..."
python -m graph_notebook.nbextensions.install

echo "installing static resources..."
python -m graph_notebook.static_resources.install

echo "enabling visualization..."
jupyter nbextension install --py --sys-prefix graph_notebook.widgets
jupyter nbextension enable  --py --sys-prefix graph_notebook.widgets

mkdir -p ~/SageMaker/Neptune
cd ~/SageMaker/Neptune || exit
python -m graph_notebook.notebooks.install
chmod -R a+rw ~/SageMaker/Neptune/*

source ~/.bashrc || exit
HOST=${GRAPH_NOTEBOOK_HOST}
PORT=${GRAPH_NOTEBOOK_PORT}
AUTH_MODE=${GRAPH_NOTEBOOK_AUTH_MODE}
SSL=${GRAPH_NOTEBOOK_SSL}
LOAD_FROM_S3_ARN=${NEPTUNE_LOAD_FROM_S3_ROLE_ARN}

if [[ ${SSL} -eq "" ]]; then
  SSL="True"
fi

echo "Creating config with
HOST:                       ${HOST}
PORT:                       ${PORT}
AUTH_MODE:                  ${AUTH_MODE}
SSL:                        ${SSL}
AWS_REGION:                 ${AWS_REGION}"

/home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/python -m graph_notebook.configuration.generate_config \
  --host "${HOST}" \
  --port "${PORT}" \
  --auth_mode "${AUTH_MODE}" \
  --ssl "${SSL}" \
  --load_from_s3_arn "${LOAD_FROM_S3_ARN}" \
  --aws_region "${AWS_REGION}"

source /home/ec2-user/anaconda3/bin/deactivate
echo "done."

EOF
