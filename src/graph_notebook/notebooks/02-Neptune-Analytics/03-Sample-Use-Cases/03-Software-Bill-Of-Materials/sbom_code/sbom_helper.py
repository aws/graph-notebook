import json
import os
import yaml

def set_nodesteam_yaml(config, directory):   
    with open(f'nodestream_template.yaml','r') as f:
        file = yaml.safe_load(f)
        
        # Set the example sbom location and strip any prefixed slashes
        directory = directory.lstrip("/")
        file['plugins'][0]['config']['paths'] = f"{file['plugins'][0]['config']['paths']}{directory}"
        
        # Set the configuration based on if this is a Neptune Database or Neptune Analytics Graph
        if config['neptune_service'] == 'neptune-graph':
            print("Setting configuration for Neptune Analytics")
            file['targets']['my-neptune']['graph_id'] = config['host'].split('.')[0]
            file['targets']['my-neptune']['mode'] = 'analytics'
        else:
            print("Setting configuration for Neptune Database")
            file['targets']['my-neptune']['graph_id'] = f"https://{config['host']}:{config['port']}"
            file['targets']['my-neptune']['region'] = config['aws_region']
            file['targets']['my-neptune']['mdoe'] = 'database'

    with open(f'nodestream.yaml','w') as f:
        yaml.dump(file, f, sort_keys = False)
    
    print("Nodestrean SBOM configuration written.")