from cfx_nodeFunctions import logictypes, animationtypes
from collections import OrderedDict
from cfx_brainClasses import Neuron, Brain


def compilebrain(toloadtext, type, sim):
    """Take the string and turn in into a brain object"""
    toload = eval(toloadtext)
    result = Brain(type, sim)
    into = []
    """create the connections from the node"""
    for nodeUID in toload["nodes"]:
        lono = toload["nodes"][nodeUID]
        if lono["type"] == "LogicNode":
            item = logictypes[lono["category"][0]](result)
        else:
            item = animationtypes[lono["category"][0]](results)
        item.parent = lono["frameparent"]
        settings = lono["settings"]
        for s in settings:
            if isinstance(settings[s], str):
                settings[s] = settings[s].replace("{NEWLINE}", "\n")
        item.settings = lono["settings"]
        result.neurons[nodeUID] = item
    # add the edges to the connections
    for edge in toload["edges"]:
        into.append(edge["dest"])
        result.neurons[edge["source"]].inputs.append(edge["dest"])
    # find the neurons that are going to start being evaulated
    for nodeUID in toload["nodes"]:
        if lono["type"] == "LogicNode" and (nodeUID not in into):
            result.outputs.append(nodeUID)
    return result
