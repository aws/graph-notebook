#!/bin/bash

sudo -u ec2-user -i <<'EOF'

echo "export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT" >> ~/.bashrc  # set to IAM instead of DEFAULT if cluster is IAM enabled
echo "export GRAPH_NOTEBOOK_SERVICE=neptune-db" >> ~/.bashrc # set to neptune-graph for Neptune Analytics host
echo "export GRAPH_NOTEBOOK_HOST=CHANGE-ME" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT=8182" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN=" >> ~/.bashrc
echo "export AWS_REGION=us-west-2" >> ~/.bashrc  # modify region if needed

NOTEBOOK_VERSION=""

source activate JupyterSystemEnv

echo "installing Python 3 kernel"
python3 -m ipykernel install --sys-prefix --name python3 --display-name "Python 3"

echo "installing python dependencies..."
pip uninstall NeptuneGraphNotebook -y # legacy uninstall when we used to install from source in s3

if [[ ${NOTEBOOK_VERSION} == "" ]]; then
  pip install --upgrade graph-notebook
else
   pip install --upgrade graph-notebook==${NOTEBOOK_VERSION}
fi

echo "installing nbextensions..."
python -m graph_notebook.nbextensions.install

echo "installing static resources..."
python -m graph_notebook.static_resources.install

echo "enabling visualization for classic notebook......"
if [[ ${NOTEBOOK_VERSION//./} < 330 ]] && [[ ${NOTEBOOK_VERSION} != "" ]]; then
    echo "Using nbextension install for version ${NOTEBOOK_VERSION} (< 3.3.0)..."
    jupyter nbextension install --py --sys-prefix graph_notebook.widgets
fi

if [[ ${NOTEBOOK_VERSION//./} < 500 ]] && [[ ${NOTEBOOK_VERSION} != "" ]]; then
    echo "Using nbextension enable for version ${NOTEBOOK_VERSION} (< 5.0.0)..."
    jupyter nbextension enable --py --sys-prefix graph_notebook.widgets
else
    echo "Using nbclassic-extension enable for version ${NOTEBOOK_VERSION} (>= 5.0.0)..."
    jupyter nbclassic-extension enable --py --sys-prefix graph_notebook.widgets || {
        echo "nbclassic-extension enable failed, trying standard nbextension as fallback..."
        jupyter nbextension enable --py --sys-prefix graph_notebook.widgets
    }
fi
echo "enabled visualization..."

echo "Copying starter notebooks..."
mkdir -p ~/SageMaker/Neptune
cd ~/SageMaker/Neptune || exit
python -m graph_notebook.notebooks.install
chmod -R a+rw ~/SageMaker/Neptune/*
echo "Copied starter notebooks..."

source ~/.bashrc || exit
HOST=${GRAPH_NOTEBOOK_HOST}
PORT=${GRAPH_NOTEBOOK_PORT}
SERVICE=${GRAPH_NOTEBOOK_SERVICE}
AUTH_MODE=${GRAPH_NOTEBOOK_AUTH_MODE}
SSL=${GRAPH_NOTEBOOK_SSL}
LOAD_FROM_S3_ARN=${NEPTUNE_LOAD_FROM_S3_ROLE_ARN}

if [[ ${SSL} -eq "" ]]; then
  SSL="True"
fi

echo "Creating config with
HOST:                       ${HOST}
PORT:                       ${PORT}
SERVICE:                    ${SERVICE}
AUTH_MODE:                  ${AUTH_MODE}
SSL:                        ${SSL}
AWS_REGION:                 ${AWS_REGION}"

/home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/python -m graph_notebook.configuration.generate_config \
  --host "${HOST}" \
  --port "${PORT}" \
  --neptune_service "${SERVICE}" \
  --auth_mode "${AUTH_MODE}" \
  --ssl "${SSL}" \
  --load_from_s3_arn "${LOAD_FROM_S3_ARN}" \
  --aws_region "${AWS_REGION}"

echo "Adding graph_notebook.magics to ipython config..."
if [[ ${NOTEBOOK_VERSION//./} > 341 ]] || [[ ${NOTEBOOK_VERSION} == "" ]]; then
  /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/python -m graph_notebook.ipython_profile.configure_ipython_profile
else
  echo "Skipping, unsupported on graph-notebook<=3.4.1"
fi

echo "graph-notebook installation complete."

conda deactivate || echo "Already deactivated or not in an environment."
echo "done."

EOF
