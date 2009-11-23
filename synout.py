# -*- coding: utf-8 -*-

import pydot
import os

import syn

class SyntaxTreePrinter(object):

    def __init__(self, trees, path):
        self.trees = trees
        self.ctr = 0
        self.graph = pydot.Dot()
        self.filename, ext = os.path.splitext(os.path.basename(path))

    @property
    def counter(self):
        res, self.ctr = self.ctr, self.ctr + 1
        return str(res)

    def write(self):

        def add_to_current(node):
            if isinstance(node, syn.SynBinaryOp):
                children = [node.opleft, node.opright]
            elif isinstance(node, syn.SynFunctionCall):
                children = [node.func] + node.args
                functions.append(node.func)
            else:
                children = []

            node_shape = "ellipse" if children != [] else "box"
            if node in functions:
                node_shape = "diamond"

            node_id = indices[node]
            self.current_graph.add_node(
                pydot.Node(node_id, label = str(node), shape = node_shape))

            if len(children) != 0:
                # нельзя добавить потомков в граф в этом же цикле, потому как
                # будет нарушен порядок добавления ребер, и при выводе
                # вместо красивого дерева получится непонятная паутина
                for child in children:
                    indices[child] = self.counter
                    self.current_graph.add_edge(pydot.Edge(node_id, indices[child]))
                map(add_to_current, children)

        indices, functions = {}, []
        for root in self.trees:
            self.current_graph = pydot.Subgraph()
            indices[root] = self.counter
            add_to_current(root)
            self.graph.add_subgraph(self.current_graph)
        self.graph.write_gif(self.filename + ".gif")


def print_symbol_table(symtable):
    for pair in symtable.items():
        print("{0}: {1}".format(pair[0], pair[1]))
