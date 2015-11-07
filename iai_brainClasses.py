from . import iai_channels as chan
import random
import functools
import bpy
import mathutils

sce = bpy.context.scene


class Impulse():
    def __init__(self, tup):
        self.key = tup[0]
        self.val = tup[1]

    """def __getitem__(self, key):
        if key == 0:
            return self.key
        if key == 1:
            return self.val"""
    # I don't think this is needed... but it might be


class ImpulseContainer():
    # TODO Isn't this just a dictionary?!?!?!
    def __init__(self, cont):
        self.cont = cont

    def __getitem__(self, key):
        if key in self.cont:
            if not isinstance(self.cont[key], Impulse):
                print("NOT IMPULSE IN CONTAINER")
            return self.cont[key]

    """def __setitem__(self, key, value):
        self.cont[key] = value
    def __delitem__(self, key):
        del self.cont[key]"""
    # This shouldn't be allowed but commented because I'm not sure if this
    # is used anywhere

    def __iter__(self):
        return iter([Impulse(x) for x in self.cont.items()])
        # This gets calculated every time the input is looked at
        # Better to calculate in __init__?

    def __contains__(self, item):
        return item in self.cont

    def __len__(self):
        return len(self.cont)

    def values(self):
        return self.cont.values()


class Neuron():
    """The representation of the nodes. Not to be used on own"""
    def __init__(self, brain, bpyNode):
        self.brain = brain
        self.neurons = self.brain.neurons
        self.inputs = []
        # self.parent = None
        self.result = None
        self.resultLog = [(0, 0, 0), (0, 0, 0)]
        # self.active = True # Don't think this is used???
        self.fillOutput = bpy.props.BoolProperty(default=True)
        self.bpyNode = bpyNode
        self.settings = {}
        self.dependantOn = []

    def evaluate(self):
        """Called by any neurons that take this neuron as an input"""
        if self.result:
            return self.result
        noDeps = len(self.dependantOn) == 0
        dep = True in [self.neurons[x].isCurrent for x in self.dependantOn]
        # Only output something if the node isn't dependant on a state
        #  or if one of it's dependancies is the current state
        if noDeps or dep:
            inps = []
            for i in self.inputs:
                got = self.neurons[i].evaluate()
                """For each of the inputs the result is collected. If the
                input in not a dictionary then it is made into one"""
                if got is not None:
                    inps.append(got)
            # print("E", self.settings, inps)
            im = self.core(inps, self.settings)
            if isinstance(im, dict):
                output = ImpulseContainer(im)
            elif isinstance(im, ImpulseContainer):
                # TODO this shouldn't be allowed
                print("iai_brainClasses.py - This should not be allowed")
                output = im
            elif im is None:
                output = im
            else:
                output = ImpulseContainer({"None": im})
        else:
            output = None
        self.result = output

        # Calculate the colour that would be displayed in the agent is selected
        total = 0
        if output:
            val = 1
            av = sum(output.values()) / len(output)
            if av > 0:
                startHue = 0.333
            else:
                startHue = 0.5

            if av > 1:
                hueChange = -(-(abs(av)+1)/abs(av) + 2) * (1/3)
                hue = 0.333 + hueChange
                sat = 1
            elif av < -1:
                hueChange = (-(abs(av)+1)/abs(av) + 2) * (1/3)
                hue = 0.5 + hueChange
                sat = 1
            else:
                hue = startHue

            if abs(av) < 1:
                sat = abs(av)**(1/2)
            else:
                sat = 1
        else:
            hue = 0
            sat = 0
            val = 0.5
        self.resultLog[-1] = (hue, sat, val)

        return output

    def newFrame(self):
        self.result = None
        self.resultLog.append((0, 0, 0.5))

    def highLight(self, frame):
        """Colour the nodes in the interface to reflect the output"""
        hue, sat, val = self.resultLog[frame]
        self.bpyNode.use_custom_color = True
        c = mathutils.Color()
        c.hsv = hue, sat, val
        self.bpyNode.color = c
        self.bpyNode.keyframe_insert("color")
        # self.bpyNode.update()


class State():
    """The basic element of the state machine. Abstract class"""
    def __init__(self, brain, bpyNode, name):
        self.name = name
        self.brain = brain
        self.neurons = self.brain.neurons
        self.outputs = []
        self.valueInputs = []  # Left empty by start state
        self.values = []  # The results from evaluating the valueInputs
        self.finalValue = 1.0
        self.settings = {}
        self.isCurrent = False

        self.length = 0
        self.currentFrame = 0

        self.bpyNode = bpyNode
        self.resultLog = [(0, 0, 0), (0, 0, 0)]

    def query(self):
        """If this state is a valid next move return float > 0"""
        return self.finalValue

    def moveTo(self):
        # print("moveto called")
        """Called when the current state moves to this node"""
        print("Moving to a new state:", self.name)
        self.currentFrame = 0
        self.isCurrent = True
        """self.currentFrame = 0
        self.isCurrent = True
        act = self.settings["Action"]  # STRING
        if act in self.tree.brain.sim.actions:
            actionobj = self.tree.brain.sim.actions[act]  # from .iai_motion.py
            obj = sce.objects[userid]  # bpy object
            tr = obj.animation_data.nla_tracks.new()  # NLA track
            action = actionobj.action  # bpy action
            if action:
                strip = tr.strips.new("", sce.frame_current, action)
                strip.extrapolation = 'NOTHING'
                strip.use_auto_blend = True
            self.length = actionobj.length"""
        """ tr = obj.animation_data.nla_tracks.new()  # NLA track
            action = actionobj.motion
            if action:
                strip = tr.strips.new("", sce.frame_current, action)
                strip.extrapolation = 'HOLD_FORWARD'
                strip.use_auto_blend = False
                strip.blend_type = 'ADD'"""

    def evaluate(self):
        """Called while all the neurons are being evaluated"""
        self.values = []
        num = 0
        for inp in self.valueInputs:
            self.values.append(self.neurons[inp].evaluate())
        if self.settings["ValueFilter"] == "AVERAGE":
            total = 0
            num = 0
        else:
            vals = []
        for v in self.values:
            if v:
                if self.settings["ValueFilter"] == "AVERAGE":
                    for i in v.values():
                        total += i
                        num += 1
                else:
                    vals += v.values()
        if num == 0:
            num = 1

        if self.settings["ValueFilter"] == "AVERAGE":
            result = total / num
        elif self.settings["ValueFilter"] == "MAX":
            result = max(vals)
        elif self.settings["ValueFilter"] == "MIN":
            result = min(vals)
        self.finalValue = result

    def evaluateState(self):
        """Return the state to move to (allowed to return itself)

        :returns: moving to new state, name of new state or None
        :rtype: bool, string | None
        """
        self.currentFrame += 1

        """Check to see if the current state is still playing an animation"""
        # print("currentFrame", self.currentFrame, "length", self.length)
        # print("Value compared", self.length - 2 - self.settings["Fade out"])
        if self.currentFrame < self.length - 1:
            return False, self.name

        options = []
        for con in self.outputs:
            val = self.neurons[con].query()
            if val:
                print(con, val)
                options.append((con, val))
        if len(options) > 0:
            self.resultLog.append((0.15, 0.25, 1.0))
            if len(options) == 1:
                return True, options[0][0]
            elif len(options) > 0:
                return True, sorted(options, key=lambda v: v[1])[-1][0]
        self.resultLog.append((0.0, 0.0, 1.0))

        return False, None

    def newFrame(self):
        pass

    def highLight(self, frame):
        pass


class Brain():
    """An executable brain object. One created per agent"""
    def __init__(self, sim, userid):
        self.userid = userid
        self.sim = sim
        self.neurons = {}
        self.outputs = []
        self.agvars = {}
        self.lvars = self.sim.lvars
        self.outvars = {}
        self.tags = {}
        self.isActiveSelection = False

        self.states = []
        self.currentState = None

    def reset(self):
        self.outvars = {"rx": 0, "ry": 0, "rz": 0,
                        "px": 0, "py": 0, "pz": 0}
        self.tags = self.sim.agents[self.userid].access["tags"]
        # self.tags = {}
        self.agvars = self.sim.agents[self.userid].agvars

    def execute(self):
        """Called for each time the agents needs to evaluate"""
        self.isActiveSelection = bpy.context.active_object.name == self.userid
        self.reset()
        for name, var in self.lvars.items():
            var.setuser(self.userid)
        for neur in self.neurons.values():
            neur.newFrame()
        for out in self.outputs:
            self.neurons[out].evaluate()
        if self.currentState:
            new, nextState = self.neurons[self.currentState].evaluateState()
            self.neurons[self.currentState].isCurrent = False
            self.currentState = nextState
            self.neurons[self.currentState].isCurrent = True
            if new:
                self.neurons[nextState].moveTo()
