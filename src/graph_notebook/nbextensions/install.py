import argparse
import os

PLUGINS = [
    'neptune_menu',
    'gremlin_syntax',
    'sparql_syntax',
    'playable_cells'
]

dir_path = os.path.dirname(os.path.realpath(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin-name', default='', type=str, help='install and enable this jupyter plugin')

    args = parser.parse_args()
    if args.plugin_name == '':
        for p in PLUGINS:
            os.system(f'''echo "installing {p}";\
                cd {dir_path}; \
                jupyter nbextension install {p} --sys-prefix --overwrite;\
                jupyter nbextension enable {p}/main --sys-prefix''')
    else:
        os.system(f'''echo "installing {args.plugin_name}";\
            cd {dir_path}; \
            jupyter nbextension install {args.plugin_name} --sys-prefix --overwrite;\
            jupyter nbextension enable {args.plugin_name}/main --sys-prefix''')


if __name__ == '__main__':
    main()
