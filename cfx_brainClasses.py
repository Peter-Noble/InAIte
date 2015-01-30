import cfx_channels as chan
import PySide


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
            if not im:
                im = {"None": 0}
            if isinstance(im, dict):
                output = ImpulseContainer(im)
            elif isinstance(im, ImpulseContainer):
                output = im
            else:
                output = ImpulseContainer({"None": im})
            return output

    def evaluateparent(self):
        """return the active state of the parent neuron"""
        return self.active


class State():
    """The basic element of the state machine"""
    def __init__(self, tree):
        self.tree = tree
        self.interupts = []
        self.connected = []
        self.default = None

        self.interupt = False
        self.start = False

    def poll(self):
        """If this state is a valid next move return float > 0"""
        return 1.0

    def evaluate(self):
        connectedhard = []
        connectedsoft = []
        for coninterupt in self.interupts:
            val = coninterupt.poll()
            if val:
                if interupt.settings["Hard interupt"]:
                    connectedhard.append((coninterupt, val))
                else:
                    connectedsoft.append((coninterupt, val))
        if len(connectedhard) > 0:
            goto = max(connectedhard, key=lambda v: v[1])
            return goto[0]
        unconnectedhard = []
        unconnectedsoft = []
        for interupt in self.tree.interupts:
            if interupt not in self.interupts:
                val = coninterupt.poll()
                if val:
                    if interupt.settings["Hard interupt"]:
                        unconnectedhard.append((coninterupt, val))
                    else:
                        unconnectedsoft.append((coninterupt, val))
        if len(unconnectedhard) > 0:
            goto = max(unconnectedhard, key=lambda v: v[1])
            return goto[0]
        # Stop at this point if animation is still going
        # TODO this needs Blender code in here (or reference to it)

        if len(connectedsoft) > 0:
            goto = max(connectedsoft, key=lambda v: v[1])
            return goto[0]

        if len(unconnectedsoft) > 0:
            goto = max(unconnectedsoft, key=lambda v: v[1])
            return goto[0]

        options = []
        for con in self.connected:
            val = con.poll()
            if val:
                options.append((con, val))
        # TODO Finish this

        # Check the brain output
        # TODO How does the brain output this data?

        # Default output
        # TODO How do you store this information in a way the user can edit?

        return

        # Go back to START


class StateTree():
    """Contains all the states"""
    def __init__(self):
        self.interupts = []
        self.states = []
        self.current = None
        self.start = None
        """current and start will begin the same but current will change"""
        self.brain = None  # Assigned when agent is compiled

    def execute(self):
        pass


class Brain():
    """An executable brain object. Only one created per group it is used in"""
    def __init__(self, type, sim, tree):
        self.tree = tree
        self.tree.brain = self
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
            var.setuser(userid)
        for out in self.outputs:
            self.neurons[out].evaluate()
