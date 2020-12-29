import argparse


def str_to_namespace_var(key: str, local_ns: dict) -> any:
    if local_ns is None:
        return key

    if type(key) is not str:
        return key

    tmp_key = key.strip()
    if not (tmp_key.startswith('${') and tmp_key.endswith('}')):
        return key
    else:
        tmp_key = tmp_key[2:-1].strip()
        return key if tmp_key not in local_ns else local_ns[tmp_key]


def replace_namespace_vars(args: argparse.Namespace, local_ns: dict):
    if local_ns is None or local_ns == {}:
        return

    for key in list(args.__dict__.keys()):
        new_value = str_to_namespace_var(args.__dict__[key], local_ns)
        args.__dict__[key] = new_value
