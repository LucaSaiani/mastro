from bpy.types import NodeTree


class MaStroScheduleTree(NodeTree):
    """MaStro Schedule node tree: build quantity-takeoff tables from the MaStro model"""
    bl_idname = 'MaStroScheduleTreeType'
    bl_label = "MaStro Schedule"
    bl_icon = 'NODETREE'

    def execute(self):
        from .execution import evaluate_tree
        evaluate_tree(self)

    def update(self):
        # Blender allows linking sockets of different bl_idname unless
        # something actively rejects the link - it does not infer
        # compatibility from socket type on its own. update() runs on every
        # topology change (including mid-drag while a link is being made),
        # so this is where mismatched links (e.g. an Attribute Ref socket
        # plugged into a Data socket) get flagged: the link itself is left
        # alone (so the user can see and fix what they wired), but every
        # node with a mismatched input is colored as a warning - mirroring
        # the old prototype's checkLink() (mastro_schedule.py), which did
        # the same by comparing socket bl_label and tinting the node dark
        # red instead of silently dropping the link or drawing custom GPU
        # warning lines.
        for node in self.nodes:
            if not isinstance(node, MaStroScheduleTreeNode):
                continue
            mismatched = any(
                socket.is_linked and socket.links
                and socket.links[0].from_socket.bl_idname != socket.bl_idname
                for socket in node.inputs
            )
            node.use_custom_color = mismatched
            if mismatched:
                node.color = (0.51, 0.19, 0.29)

        # update() is also triggered by intermediate states while a node/link
        # is being created, so evaluation errors are reported but not raised.
        try:
            self.execute()
        except Exception as exc:
            print(f"MaStro Schedule: execution error: {exc}")


class MaStroScheduleTreeNode:
    """Mixin shared by all nodes of the MaStro Schedule tree"""

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'MaStroScheduleTreeType'

    def evaluate(self, inputs):
        """Return a list of output values, one per output socket.

        `inputs` is a list of values, one per input socket (None if unlinked).
        Each value is a list of row dicts (a table).
        """
        return []
