import cfx_channels as chan
import PySide

PCol = PySide.QtCore.Qt.GlobalColor


class Impulse():
    """The object that is passed between the neurons"""
    def __init__(self, val):
        self.dictionary = isinstance(val, dict)
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

    def values(self):
        if self.dictionary:
            return self.val.values()
        else:
            return [self.val]


def combine(fr, tr):
    """fr+tr are set of keys"""
    fr = list(fr)
    tr = list(tr)
    if tr == ["None"]:
        return fr
    elif fr == ["None"]:
        return tr
    else:
        return list(set(fr+tr))


class Neuron():
    """The representation of the nodes"""
    def __init__(self, brain):
        self.brain = brain
        self.neurons = self.brain.neurons
        self.inputs = []
        self.parent = None
        self.result = None
        self.active = True

    def evaluate(self):
        """Called by any neurons that take this neuron as an input"""
        execute = True
        if self.parent:
            execute = self.neurons[self.parent].evaluateparent()
        """if the neuron has a parent then only continue if it's active"""
        if execute:
            if self.result:
                return self.result
            inps = []
            for i in self.inputs:
                got = self.neurons[i].evaluate()
                if got:
                    inps.append(got)
            keys = []
            if len(inps) > 0:
                keys = inps[0].keys()
                for f in range(len(inps)-1):
                    keys = combine(keys, inps[f+1].keys())
            """Keys contains all the keys input from all connected nodes"""
            im = self.core(keys, inps, self.settings,
                           self.brain.lvars, self.brain.gvars)
            #self.result = Impulse(im)
            return Impulse(im)

    def evaluateparent(self):
        """return the active state of the parent neuron"""
        return self.active


class Brain():
    """An executable brain object"""
    def __init__(self):
        self.neurons = {}
        self.outputs = []
        self.lvars = {}
        self.gvars = {}
        self.lvars["Noise"] = chan.Noise()
        self.lvars["Sound"] = chan.Sound()
        self.lvars["State"] = chan.State()
        self.lvars["World"] = chan.World()
        self.lvars["Crowd"] = chan.Crowd()
        self.outvars = {}

    def reset(self):
        self.outvars = {"rx": 0, "ry": 0, "rz": 0,
                        "px": 0, "py": 0, "pz": 0}

    def execute(self, userid):
        """Called for each time the agents needs to evaluate"""
        print("outputs", self.outputs)
        self.reset()
        for var in self.lvars.values():
            var.setuser(userid)
        for out in self.outputs:
            self.neurons[out].evaluate()
