# -*- coding: utf-8 -*-

import pydot
import os

from tree import SynCall

class SyntaxTreePrinter(object):
    def __init__(self, trees, path):
        self.trees = trees
        self.ctr = 0
        self.graph = pydot.Dot()
        self.filename = os.path.splitext(os.path.basename(path))[0]

    @property
    def counter(self):
        res, self.ctr = self.ctr, self.ctr + 1
        return str(res)

    def write(self):

        def add_to_current(node):
            if isinstance(node, SynCall):
                functions.append(node.caller)

            node_shape = 'ellipse' if node.children else 'box'
            if node in functions:
                node_shape = 'diamond'

            node_id = indices[node]
            self.current_graph.add_node(
                pydot.Node(node_id, label='"{0}"'.format(node.label),
                    shape=node_shape, fontname='Verdana'))

            for child in node.children:
                indices[child] = self.counter
                self.current_graph.add_edge(
                    pydot.Edge(node_id, indices[child]))
            # нельзя добавить ребра и вершины в одном цикле, потому что
            # из-за рекурсивности add_to_current() будет нарушен порядок
            # добавления ребер, и при выводе вместо красивого дерева
            # получится непонятная паутина
            map(add_to_current, node.children)

        indices, functions = {}, []
        for root in self.trees:
            self.current_graph = pydot.Subgraph()
            indices[root] = self.counter
            add_to_current(root)
            self.graph.add_subgraph(self.current_graph)
        if self.graph.get_subgraph_list():
            self.graph.write_dot(self.filename + '.dot')
            self.graph.write_gif(self.filename + '.gif')
