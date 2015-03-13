from .cfx_nodeFunctions import logictypes, statetypes
from collections import OrderedDict
from .cfx_brainClasses import Neuron, Brain, State, StateTree
import functools


def processstring(toloadtext):
    """Turn the string that is stored in the Blend"""
    toload = eval(toloadtext)
    output = {"LogicNode": {"nodes": {},
                            "edges": []},
              "MotionNode": {"nodes": {},
                             "edges": []}}
    for name, node in toload["nodes"].items():
        output[node["type"]]["nodes"][name] = node
    for edge in toload["edges"]:
        if edge["dest"] in output["LogicNode"]["nodes"]:
            output["LogicNode"]["edges"].append(edge)
        elif edge["dest"] in output["MotionNode"]["nodes"]:
            output["MotionNode"]["edges"].append(edge)
    return output


def compilestatetree(toload, brain):
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


def compilebrain(toload, category, sim, newtree):
    """Compile the brain that defines how and agent moves and is animated"""
    result = Brain(category, sim, newtree)
    """create the connections from the node"""
    for nodeUID in toload["nodes"]:
        lono = toload["nodes"][nodeUID]
        item = logictypes[lono["category"][0]](result)
        item.parent = lono["frameparent"]
        settings = lono["settings"]
        for s in settings:
            if isinstance(settings[s], str):
                settings[s] = settings[s].replace("{NEWLINE}", "\n")
        item.settings = settings
        result.neurons[nodeUID] = item
    # add the edges to the connections
    into = []  # List of nodes that have input
    for edge in toload["edges"]:
        into.append(edge["dest"])
        result.neurons[edge["source"]].inputs.append(edge["dest"])
    # find the neurons that are going to start being evaulated
    for nodeUID in toload["nodes"]:
        if lono["type"] == "LogicNode" and (nodeUID not in into):
            result.outputs.append(nodeUID)
    return result


def compileagent(toloadtext, category, sim):
    """Assemble and agent object from all the parts it needs"""
    toload = processstring(toloadtext)
    newtree = functools.partial(compilestatetree, toload["MotionNode"])
    brain = compilebrain(toload["LogicNode"], category, sim, newtree)
    return brain
