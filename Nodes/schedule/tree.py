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
