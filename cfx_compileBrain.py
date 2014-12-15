from cfx_nodeFunctions import logictypes, animationtypes
from collections import OrderedDict
from cfx_brainClasses import Neuron, Brain


def compilebrain(toloadtext):
    """Take the string that node graphs are saved to and turn in into a brain object"""
    toload = eval(toloadtext)
    result = Brain()
    into = []
    #create the connections from the node
    for nodeUID in toload["nodes"]:
        if toload["nodes"][nodeUID]["type"] == "LogicNode":
            item = logictypes[toload["nodes"][nodeUID]["category"][0]](result)
        else:
            item = animationtypes[toload["nodes"][nodeUID]["category"][0]](result)
        item.parent = toload["nodes"][nodeUID]["frameparent"]
        item.settings = toload["nodes"][nodeUID]["settings"]
        result.neurons[nodeUID] = item
    #add the edges to the connections
    for edge in toload["edges"]:
        into.append(edge["dest"])
        result.neurons[edge["source"]].inputs.append(edge["dest"])
    #find the neurons that are going to start being evaulated
    for nodeUID in toload["nodes"]:
        if toload["nodes"][nodeUID]["type"] == "LogicNode" and (nodeUID not in into):
            result.outputs.append(nodeUID)
    return result