"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from gremlin_python.structure.io.graphsonV3d0 import MapType


# Original code from Tinkerpop 3.4.1
#
# class MapType(_GraphSONTypeIO):
#     python_type = DictType
#     graphson_type = "g:Map"
#
#     @classmethod
#     def dictify(cls, d, writer):
#         l = []
#         for key in d:
#             l.append(writer.toDict(key))
#             l.append(writer.toDict(d[key]))
#         return GraphSONUtil.typedValue("Map", l)
#
#     @classmethod
#     def objectify(cls, l, reader):
#         new_dict = {}
#         if len(l) > 0:
#             x = 0
#             while x < len(l):
#                 new_dict[reader.toObject(l[x])] = reader.toObject(l[x + 1])
#                 x = x + 2
#         return new_dict

class MapType_patch:
    @classmethod
    def objectify(cls, l, reader):  # noqa E741
        new_dict = {}
        if len(l) > 0:
            x = 0
            while x < len(l):
                tmp = reader.toObject(l[x])
                # Avoid keys that are dicts by making them tuples
                if type(tmp) == dict:
                    tmp = tuple([(k, v) for k, v in tmp.items()])
                new_dict[tmp] = reader.toObject(l[x + 1])
                x = x + 2
        return new_dict


MapType.objectify = MapType_patch.objectify
