# https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar

rm -rf /tmp/blazegraph*
pkill -f blazegraph

cd /tmp || exit
curl -OL https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.tar.gz
tar xvzf blazegraph.tar.gz

echo "{
  \"host\": \"$(hostname -i)\",
  \"port\": 9999,
  \"auth_mode\": \"DEFAULT\",
  \"iam_credentials_provider_type\": \"ROLE\",
  \"load_from_s3_arn\": \"\",
  \"ssl\": false,
  \"aws_region\": \"us-east-1\"
}" > /tmp/graph_notebook_config_integration_test.json