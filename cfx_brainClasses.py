import cfx_channels as chan
import PySide
import random


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
    """The representation of the nodes. Not to be used on own"""
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
    """The basic element of the state machine. Not to be used on own"""
    def __init__(self, tree):
        self.tree = tree
        self.interupts = []
        self.connected = []

        self.interupt = False
        self.start = False

        self.currentframe = 0
        self.length = 0

    def poll(self):
        """If this state is a valid next move return float > 0"""
        return 1.0

    def moveto(self):
        """Called when the current state moves to this node"""
        self.currentframe = 0

    def evaluate(self):
        """Return the state to move to (allowed to return itself)"""
        def pickfromlist(options):
            """options in form [(state, value)]"""
            if len(options) == 1:
                return options[0][0]
            elif len(options) > 0:
                """If there is more than one possible jump select one randomly
                weighted by the value that polling them returned"""
                so = sorted(options, key=lambda v: v[1])
                final = [x for x in so if x[1] == so[0][1]]
                if len(final) == 1:
                    return final[0][0]
                totals = []
                running_total = 0

                for w in final:
                    running_total += w[1]
                    totals.append(running_total)

                rnd = random.random() * running_total
                for i, total in enumerate(totals):
                    if rnd < total:
                        return final[i][0]

        """Check if there are any connected interupts to jump to"""
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
            return pickfromlist(connectedhard)
        """Check if there are any unconnected interupts to jump to"""
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
            return pickfromlist(unconnectedhard)

        """Check to see if the current state is still playing an animation"""
        if self.currentframe < self.length - self.settings["Fade out"]:
            self.currentframe += 1
            return self
        # TODO Blender code needed in here to update the current frame

        """Check to see if there are interupts to jump to that are soft"""
        if len(connectedsoft) > 0:
            return pickfromlist(unconnectedhard)

        if len(unconnectedsoft) > 0:
            return pickfromlist(unconnectedsoft)

        """If the animation is finished and no interupts look at connections"""
        options = []
        for con in self.connected:
            val = con.poll()
            if val:
                options.append((con, val))
        if len(options) > 0:
            return pickfromlist(options)

        return self.tree.start


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
        if self.current:
            cur = self.current.evaluate()
            if self.current != cur:
                cur.moveto()
                self.current = cur
                print("Moving into new state", cur.__class__.__name__)


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
        self.tree.execute()
