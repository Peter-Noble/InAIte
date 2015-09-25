import bpy
from bpy.types import NodeTree, Node, NodeSocket

from bpy.props import FloatProperty, StringProperty, BoolProperty
from bpy.props import EnumProperty, IntProperty


class InAIteTree(NodeTree):
    # Description string
    """New type of node tree to contain the InAIte nodes"""
    # If not explicitly defined, the python class name is used.
    bl_idname = 'InAIteTreeType'
    # Label for nice name display
    bl_label = 'InAIte Node Tree'
    # Icon identifier
    bl_icon = 'MOD_ARMATURE'


class DefaultSocket(NodeSocket):
    # Description string
    """Default socket"""
    # If not explicitly defined, the python class name is used.
    bl_idname = 'DefaultSocketType'
    # Label for nice name display
    bl_label = 'Default Node Socket'

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text)
        """if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "myEnumProperty", text=text)"""

    # Socket color
    def draw_color(self, context, node):
        return (0.0, 0.0, 0.0, 0.4)


class InAIteNode(Node):
    """InAIte nodes superclass"""
    # bl_idname = 'CustomNodeType'  # Class name used if not defined
    # Label for nice name display
    bl_label = 'Super class'
    # bl_icon = 'SOUND'

    def init(self, context):
        self.inputs.new("DefaultSocketType", "Input")
        self.inputs[0].link_limit = 4095

        self.outputs.new('DefaultSocketType', "Output")

    """# Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        pass"""

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'InAIteTreeType'


class InputNode(InAIteNode):
    """InAIte input node"""
    bl_label = "Input"

    Input = StringProperty(default="Noise.random")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Input")
        # layout.prop(self, "fillOutput")

    def get_settings(self, node):
        node.settings["Input"] = self.Input


def update_properties(self, context):
    """Keeps the values in the graph node in the correct order"""
    if self.UpperZero < self.UpperOne:
        self.UpperOne = self.UpperZero
    if self.UpperOne < self.LowerOne:
        self.LowerOne = self.UpperOne
    if self.LowerOne < self.LowerZero:
        self.LowerZero = self.LowerOne


class GraphNode(InAIteNode):
    """InAIte graph node"""
    bl_label = "Graph"

    CurveType = EnumProperty(items=[("RBF", "RBF", "", 1),
                                    ("RANGE", "Range", "", 2)
                                    ])

    LowerZero = FloatProperty(default=-1.0, update=update_properties)
    LowerOne = FloatProperty(default=-0.5, update=update_properties)
    UpperOne = FloatProperty(default=0.5, update=update_properties)
    UpperZero = FloatProperty(default=1.0, update=update_properties)

    RBFMiddle = FloatProperty(default=0.0)
    RBFTenPP = FloatProperty(default=0.25)  # Ten percent point

    def draw_buttons(self, context, layout):
        layout.prop(self, "CurveType", expand=True)
        if self.CurveType == "RBF":
            layout.prop(self, "RBFMiddle")
            layout.prop(self, "RBFTenPP")
        elif self.CurveType == "RANGE":
            layout.prop(self, "LowerZero")
            layout.prop(self, "LowerOne")
            layout.prop(self, "UpperOne")
            layout.prop(self, "UpperZero")

    def get_settings(self, node):
        node.settings["CurveType"] = self.CurveType
        node.settings["LowerZero"] = self.LowerZero
        node.settings["LowerOne"] = self.LowerOne
        node.settings["UpperOne"] = self.UpperOne
        node.settings["UpperZero"] = self.UpperZero
        node.settings["RBFMiddle"] = self.RBFMiddle
        node.settings["RBFTenPP"] = self.RBFTenPP


class AndNode(InAIteNode):
    """InAIte and node"""
    bl_label = "And"

    SingleOutput = BoolProperty(default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "SingleOutput")

    def get_settings(self, node):
        node.settings["SingleOutput"] = self.SingleOutput


class OrNode(InAIteNode):
    """InAIte or node"""
    bl_label = "Or"

    SingleOutput = BoolProperty(default=True)

    def draw_buttons(self, context, layout):
        layout.prop(self, "SingleOutput")

    def get_settings(self, node):
        node.settings["SingleOutput"] = self.SingleOutput


class QueryTagNode(InAIteNode):
    """InAIte Query Tag node"""
    bl_label = "Query Tag"

    Tag = StringProperty(default="default")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Tag")

    def get_settings(self, node):
        node.settings["Tag"] = self.Tag


class SetTagNode(InAIteNode):
    """InAIte Set Tag node"""
    bl_label = "Set Tag"

    Tag = StringProperty(default="default")
    UseThreshold = BoolProperty(default=True)
    Threshold = FloatProperty(default=0.5)
    Action = EnumProperty(items=[("ADD", "Add", "", 1),
                                 ("REMOVE", "Remove", "", 2)
                                 ])

    def draw_buttons(self, context, layout):
        layout.prop(self, "Tag")
        layout.prop(self, "UseThreshold")
        if self.UseThreshold:
            layout.prop(self, "Threshold")
        layout.prop(self, "Action")

    def get_settings(self, node):
        node.settings["Tag"] = self.Tag
        node.settings["UseThreshold"] = self.UseThreshold
        node.settings["Threshold"] = self.Threshold
        node.settings["Action"] = self.Action


class VariableNode(InAIteNode):
    """InAIte Variable node"""
    bl_label = "Variable"

    Variable = StringProperty(default="None")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Variable")

    def get_settings(self, node):
        node.settings["Variable"] = self.Variable


class MapNode(InAIteNode):
    """InAIte Map node"""
    bl_label = "Map"

    LowerInput = FloatProperty(default=0.0)
    UpperInput = FloatProperty(default=1.0)
    LowerOutput = FloatProperty(default=0.0)
    UpperOutput = FloatProperty(default=2.0)

    def draw_buttons(self, context, layout):
        layout.prop(self, "LowerInput")
        layout.prop(self, "UpperInput")
        layout.prop(self, "LowerOutput")
        layout.prop(self, "UpperOutput")

    def get_settings(self, node):
        node.settings["LowerInput"] = self.LowerInput
        node.settings["UpperInput"] = self.UpperInput
        node.settings["LowerOutput"] = self.LowerOutput
        node.settings["UpperOutput"] = self.UpperOutput


class OutputNode(InAIteNode):
    """InAIte Output node"""
    bl_label = "Output"

    Output = EnumProperty(items=[("rz", "rz", "", 3),
                                 ("rx", "rx", "", 1),
                                 ("ry", "ry", "", 2),
                                 ("px", "px", "", 4),
                                 ("py", "py", "", 5),
                                 ("pz", "pz", "", 6)
                                 ])
    MultiInputType = EnumProperty(items=[("AVERAGE", "Average", "", 1),
                                         ("MAX", "Max", "", 2),
                                         ("SIZEAVERAGE", "Size Average", "", 3)
                                         ])

    def draw_buttons(self, context, layout):
        layout.prop(self, "Output")
        layout.prop(self, "MultiInputType")

    def get_settings(self, node):
        node.settings["Output"] = self.Output
        node.settings["MultiInputType"] = self.MultiInputType


class EventNode(InAIteNode):
    """InAIte Event node"""
    bl_label = "Event"

    EventName = bpy.props.StringProperty(default="default")

    def draw_buttons(self, context, layout):
        layout.prop(self, "EventName")

    def get_settings(self, node):
        node.settings["EventName"] = self.EventName


class PythonNode(InAIteNode):
    """InAIte Python node"""
    bl_label = "Python"

    Expression = bpy.props.StringProperty(default="output = Noise.random")
    # This really needs to link to a text block

    def draw_buttons(self, context, layout):
        layout.prop(self, "Expression")

    def get_settings(self, node):
        node.settings["Expression"] = self.Expression


class PrintNode(InAIteNode):
    """InAIte Print Node"""
    bl_label = "Print"

    Label = bpy.props.StringProperty(default="")
    # PrintSelected = bpy.props.BoolProperty(default=True)  # Not implemented

    def draw_buttons(self, context, layout):
        layout.prop(self, "Label")

    def get_settings(self, node):
        node.settings["Label"] = self.Label

# # # Node Categories # # #
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem


# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type
class MyNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'InAIteTreeType'

# all categories in a list
node_categories = [
    MyNodeCategory("BASIC", "Basic", items=[
        NodeItem("InputNode"),
        NodeItem("GraphNode"),
        NodeItem("AndNode"),
        NodeItem("OrNode"),
        NodeItem("MapNode"),
        NodeItem("OutputNode")
        ]),
    MyNodeCategory("OTHER", "Other", items=[
        NodeItem("QueryTagNode"),
        NodeItem("SetTagNode"),
        NodeItem("VariableNode"),
        NodeItem("EventNode")
        ]),
    MyNodeCategory("DEVELOPER", "Developer", items=[
        NodeItem("PythonNode"),
        NodeItem("PrintNode")
        ]),
    MyNodeCategory("LAYOUT", "Layout", items=[
        NodeItem("NodeFrame"),
        NodeItem("NodeReroute")
    ])
    ]


def register():
    bpy.utils.register_class(InAIteTree)
    bpy.utils.register_class(DefaultSocket)
    bpy.utils.register_class(InAIteNode)

    bpy.utils.register_class(InputNode)
    bpy.utils.register_class(GraphNode)
    bpy.utils.register_class(AndNode)
    bpy.utils.register_class(OrNode)
    bpy.utils.register_class(QueryTagNode)
    bpy.utils.register_class(SetTagNode)
    bpy.utils.register_class(VariableNode)
    bpy.utils.register_class(MapNode)
    bpy.utils.register_class(OutputNode)
    bpy.utils.register_class(EventNode)
    bpy.utils.register_class(PythonNode)
    bpy.utils.register_class(PrintNode)

    nodeitems_utils.register_node_categories("InAIte_NODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("InAIte_NODES")

    bpy.utils.unregister_class(InAIteTree)
    bpy.utils.unregister_class(DefaultSocket)
    bpy.utils.unregister_class(InAIteNode)

    bpy.utils.unregister_class(InputNode)
    bpy.utils.unregister_class(GraphNode)
    bpy.utils.unregister_class(AndNode)
    bpy.utils.unregister_class(OrNode)
    bpy.utils.unregister_class(QueryTagNode)
    bpy.utils.unregister_class(SetTagNode)
    bpy.utils.unregister_class(VariableNode)
    bpy.utils.unregister_class(MapNode)
    bpy.utils.unregister_class(OutputNode)
    bpy.utils.unregister_class(EventNode)
    bpy.utils.unregister_class(PythonNode)
    bpy.utils.unregister_class(PrintNode)


if __name__ == "__main__":
    register()
