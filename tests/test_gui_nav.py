class TreeDataAdapter:
    """Exercise navigation saving without opening a desktop window."""

    def __init__(self, roots):
        self.roots = [node['id'] for node in roots]
        self.nodes = {}

        def collect(nodes):
            for node in nodes:
                self.nodes[node['id']] = node
                collect(node['children'])

        collect(roots)

    def get_roots(self):
        return self.roots

    def get_children(self, item_id):
        return [node['id'] for node in self.nodes[item_id]['children']]


