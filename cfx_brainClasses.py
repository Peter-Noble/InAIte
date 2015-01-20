import cfx_channels as chan
import PySide

PCol = PySide.QtCore.Qt.GlobalColor


class Impulse():
    def __init__(self, tup):
        self.key = tup[0]
        self.val = tup[1]

    def __getitem__(self, key):
        if key == 0:
            return self.key
        if key == 1:
            return self.val


class ImpulseContainer():
    def __init__(self, cont):
        self.cont = cont

    def __getitem__(self, key):
        if key in self.cont:
            return self.cont[key]

    def __setitem__(self, key, value):
        self.cont[key] = value

    def __delitem__(self, key):
        del self.cont[key]

    def __iter__(self):
        return iter([Impulse(x) for x in self.cont.items()])

    def __contains__(self, item):
        return item in self.cont


class Neuron():
    """The representation of the nodes"""
    def __init__(self, brain):
        self.brain = brain
        self.neurons = self.brain.neurons
        self.inputs = []
        # self.parent = None
        self.result = None
        self.active = True

    def evaluate(self):
        """Called by any neurons that take this neuron as an input"""
        execute = True
        # if self.parent:
        #    execute = self.neurons[self.parent].evaluateparent()
        # """if the neuron has a parent then only continue if it's active"""
        if execute:
            if self.result:
                return self.result
            inps = []
            for i in self.inputs:
                got = self.neurons[i].evaluate()
                """For each of the inputs the result is collected. If the
                input in not a dictionary then it is made into one"""
                if got:
                    inps.append(got)
            im = self.core(inps, self.settings)
            if isinstance(im, dict):
                if not im:
                    im = {"None": 0}
                output = ImpulseContainer(im)
            elif isinstance(im, ImpulseContainer):
                output = im
            else:
                output = ImpulseContainer({"None": im})
            return output

    def evaluateparent(self):
        """return the active state of the parent neuron"""
        return self.active


class Brain():
    """An executable brain object. Only one created per group it is used in"""
    def __init__(self, type, sim):
        self.sim = sim
        self.type = type
        self.neurons = {}
        self.outputs = []
        self.agvars = {}
        self.lvars = self.sim.lvars
        self.outvars = {}
        self.tags = {}

    def reset(self):
        self.outvars = {"rx": 0, "ry": 0, "rz": 0,
                        "px": 0, "py": 0, "pz": 0}
        self.tags = self.sim.agents[self.currentuser].access["tags"]
        self.agvars = self.sim.agents[self.currentuser].agvars

    def execute(self, userid):
        """Called for each time the agents needs to evaluate"""
        self.currentuser = userid
        self.reset()
        for name, var in self.lvars.items():
            print("brainClasses", name)
            var.setuser(userid)
        for agent in self.sim.agents.values():
            for tag in agent.access["tags"]:
                print("brainClasses", agent.id, tag)
                for channel in self.lvars:
                    if tag[:len(channel)] == channel:
                        print("registering", agent.id)
                        self.lvars[channel].register(agent, tag[len(channel):],
                                                     agent.access["tags"][tag])
        for out in self.outputs:
            self.neurons[out].evaluate()
