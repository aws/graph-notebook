"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

# Backport from TinkerPop 3.5.0 pre-release
# https://github.com/apache/tinkerpop/blob/master/gremlin-python/src/main/python/gremlin_python/structure/io/util.py
# https://github.com/apache/tinkerpop/pull/1314/files
# https://github.com/apache/tinkerpop/pull/1383/files


class HashableDict(dict):
    def __hash__(self):
        try:
            return hash(tuple(sorted(self.items())))
        except:
            return hash(tuple(sorted(str(x) for x in self.items())))

    @classmethod
    def of(cls, o):
        if isinstance(o, (tuple, set, list)):
            return tuple([cls.of(e) for e in o])
        elif not isinstance(o, (dict, HashableDict)):
            return o

        new_o = HashableDict()
        for k, v in o.items():
            if isinstance(k, (set, list)):
                new_o[tuple(k)] = cls.of(v)
            else:
                new_o[k] = cls.of(v)
        return new_o
