import bpy

from .iai_nodeFunctions import logictypes, statetypes
from collections import OrderedDict
from .iai_brainClasses import Neuron, Brain, State, StateTree
import functools


def getInput(socket):
    print("Got here")
    fr = socket.links[0].from_node
    if fr.bl_idname == "NodeReroute":
        return getInput(fr.inputs[0])
    else:
        return fr.name


def compilestatetree(toload, brain):
    """Compile the state machine that is used for the animation of an agent"""
    tree = StateTree(brain)
    # TODO ...
    return tree


def compilebrain(category, sim, newtree):
    """Compile the brain that defines how and agent moves and is animated"""
    result = Brain(category, sim, newtree)
    """create the connections from the node"""
    for node in bpy.data.node_groups[category].nodes:
        if node.bl_idname != "NodeReroute" and node.bl_idname != "NodeFrame":
            # node.name  -  The identifier
            # node.bl_idname  -  The type
            item = logictypes[node.bl_idname](result, node)
            item.parent = "NOT IMPLEMENTED"
            item.settings = {}
            node.get_settings(item)
            for inp in node.inputs:
                if inp.links:
                    item.inputs.append(getInput(inp))
            result.neurons[node.name] = item
            hasOutputs = False
            for out in node.outputs:
                if out.links:
                    hasOutputs = True
            if not hasOutputs:
                result.outputs.append(node.name)
    return result


def compileagent(brainGroup, sim):
    """Assemble and agent object from all the parts it needs"""
    newtree = functools.partial(compilestatetree, None)  # TODO add state trees
    brain = compilebrain(brainGroup.name, sim, newtree)
    return brain


def compilestatetreeOLD(toload, brain):
    """For PySide version"""
    """Compile the state machine that is used for the animation of an agent"""
    tree = StateTree(brain)
    ref = {}  # Temp storage for adding edges
    for nodeUID in toload["nodes"]:
        lono = toload["nodes"][nodeUID]
        item = statetypes[lono["category"][0]](tree)  # create state object
        settings = lono["settings"]
        for s in settings:
            if isinstance(settings[s], str):
                settings[s] = settings[s].replace("{NEWLINE}", "\n")
        item.settings = settings
        if item.start:
            if tree.current:
                print("More than one start node isn't supported at the moment")
            else:
                tree.current = item
                tree.start = item
        if item.interrupt:
            tree.interrupts.append(item)
        tree.states.append(item)
        ref[nodeUID] = item
    if not tree.current and len(toload["nodes"]) > 0:
        raise Exception("Needs a start node")
    for edge in toload["edges"]:
        ref[edge["dest"]].connected.append(ref[edge["source"]])
        if ref[edge["source"]].interrupt:
            reg[edge["dest"]].interrupts.append(re[edge["source"]])
    return tree
