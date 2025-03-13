import os
import sys
import json
from pathlib import Path
import shutil
from jupyter_core.paths import jupyter_path

def check_paths():
    # Get development paths
    dev_root = os.getcwd()
    dev_widget_dir = os.path.join(dev_root, 'src', 'graph_notebook', 'widgets')
    
    # Get installation paths
    site_packages = [p for p in sys.path if 'site-packages' in p][0]
    install_widget_dir = os.path.join(site_packages, 'graph_notebook', 'widgets')
    
    # Get jupyter paths
    jupyter_paths = jupyter_path()
    lab_extension_dir = os.path.join(jupyter_paths[0], 'labextensions', 'graph_notebook_widgets')
    nb_extension_dir = os.path.join(jupyter_paths[0], 'nbextensions', 'graph_notebook_widgets')

    paths = {
        'Development': {
            'root': dev_widget_dir,
            'lab': os.path.join(dev_widget_dir, 'labextension'),
            'nb': os.path.join(dev_widget_dir, 'nbextension'),
            'lib': os.path.join(dev_widget_dir, 'lib'),
        },
        'Installed': {
            'root': install_widget_dir,
            'lab': os.path.join(install_widget_dir, 'labextension'),
            'nb': os.path.join(install_widget_dir, 'nbextension'),
            'lib': os.path.join(install_widget_dir, 'lib'),
        },
        'Jupyter': {
            'lab': lab_extension_dir,
            'nb': nb_extension_dir
        }
    }

    def print_dir_content(path, indent=''):
        if not os.path.exists(path):
            print(f"{indent}❌ Path does not exist: {path}")
            return
        
        print(f"{indent}📁 {path}")
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    print_dir_content(item_path, indent + '  ')
                else:
                    size = os.path.getsize(item_path)
                    print(f"{indent}  📄 {item} ({size} bytes)")
        except Exception as e:
            print(f"{indent}  ⚠️ Error reading directory: {e}")

    def compare_files(path1, path2, file_path):
        """Compare two files and return True if they are identical"""
        if not os.path.exists(path1) or not os.path.exists(path2):
            return False
        return filecmp.cmp(path1, path2)

    print("\n=== Development Environment ===")
    for key, path in paths['Development'].items():
        print(f"\n--- {key} ---")
        print_dir_content(path)

    print("\n=== Installed Package ===")
    for key, path in paths['Installed'].items():
        print(f"\n--- {key} ---")
        print_dir_content(path)

    print("\n=== Jupyter Directories ===")
    for key, path in paths['Jupyter'].items():
        print(f"\n--- {key} ---")
        print_dir_content(path)

    # Check critical files
    critical_files = [
        'labextension/static/remoteEntry.js',
        'labextension/package.json',
        'nbextension/extension.js',
        'nbextension/index.js',
        'lib/index.js',
    ]

    print("\n=== Critical Files Check ===")
    for file_path in critical_files:
        dev_file = os.path.join(dev_widget_dir, file_path)
        inst_file = os.path.join(install_widget_dir, file_path)
        
        print(f"\nChecking {file_path}:")
        print(f"Development: {'✅ Exists' if os.path.exists(dev_file) else '❌ Missing'}")
        print(f"Installed: {'✅ Exists' if os.path.exists(inst_file) else '❌ Missing'}")
        
        if os.path.exists(dev_file) and os.path.exists(inst_file):
            if compare_files(dev_file, inst_file):
                print("✅ Files are identical")
            else:
                print("⚠️ Files are different")

if __name__ == "__main__":
    check_paths()
