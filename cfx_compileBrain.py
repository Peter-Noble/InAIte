from cfx_nodeFunctions import logictypes, animationtypes
from collections import OrderedDict


class Transfer():
    """The object that is passed between the nodes"""
    def __init__(self, val):
        self.dictionary = type(val) == type(dict())
        self.val = val

    def __getitem__(self, key):
        if self.dictionary:
            return self.val[key]
        else:
            return self.val

    def __iter__(self):
        if self.dictionary:
            return iter(self.val)
        else:
            return iter(["None"])

    def keys(self):
        if self.dictionary:
            return self.val.keys()
        else:
            return ["None"]


def combine(fr, tr):
    """fr+tr are set of keys"""
    if tr == ["None"]:
        return fr
    elif fr == ["None"]:
        return tr
    else:
        return list(set(fr+tr))


class Connection():
    """The representation of the nodes"""
    def __init__(self, brain):
        self.brain = brain
        self.nodes = self.brain.nodes
        self.inputs = []
        self.parent = None
        #self.core is assigned during compilebrain()
        #self.settings is assigned during compilebrain()
        self.result = None

    def evaluate(self):
        execute = True
        if self.parent:
            execute = self.nodes[self.parent].evaluateparent()
        if execute:
            if self.result:
                return self.result
            inps = []
            for i in self.inputs:
                got = self.nodes[i].evaluate()
                if got:
                    inps.append(got)
            keys = []
            if len(inps) > 0:
                keys = inps[0].keys()
                for f in range(len(inps)-1):
                    keys = combine(keys, inps[f+1])
            self.result = Transfer(self.core(keys, inps, self.settings))
            return self.result
        return None
        #return the output of the node

    def evaluateparent(self):
        return True
        #return if the parent active TRUE or FALSE


class Brain():
    def __init__(self):
        self.nodes = {}
        self.outputs = []

    def execute(self):
        for out in self.outputs:
            print(self.nodes[out].core)
            self.nodes[out].evaluate()


def compilebrain(toloadtext):
    toload = eval(toloadtext)
    result = Brain()
    into = []
    #create the connections from the node
    for nodeUID in toload["nodes"]:
        item = Connection(result)
        item.parent = toload["nodes"][nodeUID]["frameparent"]
        if toload["nodes"][nodeUID]["type"] == "LogicNode":
            item.core = logictypes[toload["nodes"][nodeUID]["category"][0]].core
        else:
            item.core = animationtypes[toload["nodes"][nodeUID]["category"][0]].core
        item.settings = toload["nodes"][nodeUID]["settings"]
        result.nodes[nodeUID] = item
    #add the edges to the connections
    for edge in toload["edges"]:
        into.append(edge["dest"])
        result.nodes[edge["source"]].inputs.append(edge["dest"])
    #find the nodes that are going to start being evaulated
    for nodeUID in toload["nodes"]:
        if toload["nodes"][nodeUID]["type"] == "LogicNode" and (nodeUID not in into):
            result.outputs.append(nodeUID)
    return result