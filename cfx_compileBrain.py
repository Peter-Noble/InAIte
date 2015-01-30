from cfx_nodeFunctions import logictypes, statetypes
from collections import OrderedDict
from cfx_brainClasses import Neuron, Brain, State, StateTree


def processstring(toloadtext):
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


def compilestatetree(toload):
    tree = StateTree()
    for nodeUID in toload["nodes"]:
        lono = toload["nodes"][nodeUID]
        item = statetypes[lono["category"][0]](tree)
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

        if item.interupt:
            tree.interupts.append(item)
        tree.states.append(item)
        # TODO  FINISH!!!!!!!!!!!!!
    return tree


def compilebrain(toload, category, sim, tree):
    result = Brain(category, sim, tree)
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
    toload = processstring(toloadtext)
    tree = compilestatetree(toload["MotionNode"])
    brain = compilebrain(toload["LogicNode"], category, sim, tree)
    return brain
