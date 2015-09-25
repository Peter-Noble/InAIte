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
        # self.active = True # Don't think this is used???
        self.fillOutput = bpy.props.BoolProperty(default=True)
        self.bpyNode = bpyNode

    def evaluate(self):
        """Called by any neurons that take this neuron as an input"""
        execute = True
        # if self.parent:
        #     execute = self.neurons[self.parent].evaluateparent()
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
                # TODO this check seems to be done twice
            self.result = output
            # This next section is for the visual feedback on the node editor
            if self.brain.isActiveSelection:
                self.bpyNode.use_custom_color = True
                total = 0
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
                c = mathutils.Color()
                c.hsv = hue, sat, 1
                self.bpyNode.color = c
                self.bpyNode.keyframe_insert("color")
                # self.bpyNode.update()
            return output

    def newFrame(self):
        self.result = None
    # def evaluateparent(self):
    #     """return the active state of the parent neuron"""
    #     return self.active


class State():
    """The basic element of the state machine. Not to be used on own"""
    def __init__(self, tree):
        self.tree = tree
        self.interrupts = []
        self.connected = []

        self.interrupt = False
        self.start = False

        self.currentframe = 0
        self.length = 0

    def query(self):
        """If this state is a valid next move return float > 0"""
        return 1.0

    def moveto(self, userid):
        # print("moveto called")
        """Called when the current state moves to this node"""
        self.currentframe = 0
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
            self.length = actionobj.length
            """tr = obj.animation_data.nla_tracks.new()  # NLA track
            action = actionobj.motion
            if action:
                strip = tr.strips.new("", sce.frame_current, action)
                strip.extrapolation = 'HOLD_FORWARD'
                strip.use_auto_blend = False
                strip.blend_type = 'ADD'"""

    def active(self, currentframe):
        """Used for states that are still having an effect on the position
        and animation but aren't the current state"""
        # print("active called", self)
        fr = currentframe + 1
        if fr <= self.length:
            action = self.tree.brain.sim.actions[self.settings["Action"]]
            if "rotation_euler" in action.motiondata:
                rot = action.motiondata["rotation_euler"]
                if not fr >= len(rot[0]):
                    self.tree.brain.outvars["rx"] += rot[0][fr] - rot[0][fr-1]
                    self.tree.brain.outvars["ry"] += rot[1][fr] - rot[1][fr-1]
                    self.tree.brain.outvars["rz"] += rot[2][fr] - rot[2][fr-1]
            if "location" in action.motiondata:
                loc = action.motiondata["location"]
                if not fr >= len(loc[0]):
                    self.tree.brain.outvars["px"] += loc[0][fr] - loc[0][fr-1]
                    self.tree.brain.outvars["py"] += loc[1][fr] - loc[1][fr-1]
                    self.tree.brain.outvars["pz"] += loc[2][fr] - loc[2][fr-1]
            return fr
        else:
            return False

    # def evaluateparent(self):
    #     """return the active state of the parent neuron"""
    #     return self.currentframe != 0

    def evaluate(self):
        # print("Evaluating state", self)
        """Return the state to move to (allowed to return itself)"""
        def pickfromlist(options):
            """options in form [(state, value)]"""
            if len(options) == 1:
                return options[0][0]
            elif len(options) > 0:
                """If there is more than one possible jump select one randomly
                weighted by the value that querying them returned"""
                """so = sorted(options, key=lambda v: v[1])
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
                        return final[i][0]"""
                # I don't think this should be random
                # The user can add random with a random input node
                return sorted(options, key=lambda v: v[1])[-1][0]

        self.currentframe += 1

        """Check if there are any connected interrupts to jump to"""
        connectedhard = []
        connectedsoft = []
        for coninterrupt in self.interrupts:
            val = coninterrupt.query()
            if val:
                if interrupt.settings["Hard interrupt"]:
                    connectedhard.append((coninterrupt, val))
                else:
                    connectedsoft.append((coninterrupt, val))
        if len(connectedhard) > 0:
            # print("Return 1")
            return pickfromlist(connectedhard)
        """Check if there are any unconnected interrupts to jump to"""
        unconnectedhard = []
        unconnectedsoft = []
        for interrupt in self.tree.interrupts:
            if interrupt not in self.interrupts:
                val = coninterrupt.query()
                if val:
                    if interrupt.settings["Hard interrupt"]:
                        unconnectedhard.append((coninterrupt, val))
                    else:
                        unconnectedsoft.append((coninterrupt, val))
        if len(unconnectedhard) > 0:
            # print("Return 2")
            return pickfromlist(unconnectedhard)

        """Check to see if the current state is still playing an animation"""
        # print("currentframe", self.currentframe, "length", self.length)
        # print("Value compared", self.length - 2 - self.settings["Fade out"])
        if self.currentframe < self.length - 2 - self.settings["Fade out"]:
            # print("Return 3")
            return self

        """Check to see if there are interrupts to jump to that are soft"""
        if len(connectedsoft) > 0:
            # print("Return 4")
            return pickfromlist(unconnectedhard)

        if len(unconnectedsoft) > 0:
            # print("Return 5")
            return pickfromlist(unconnectedsoft)

        """If animation finished and no interrupts look at connections"""
        options = []
        for con in self.connected:
            val = con.query()
            if val:
                options.append((con, val))
        if len(options) > 0:
            # print("Return 6")
            # print(options)
            return pickfromlist(options)

        return self.tree.start


class StateTree():
    """Contains all the states"""
    def __init__(self, brain):
        # TODO each agent now has its own StateTree so userid could be stored
        self.brain = brain
        self.interrupts = []
        self.states = []
        self.active = []
        self.current = None
        self.start = None
        """current and start will begin the same but current will change"""

    def execute(self, userid):
        tmp = []
        if self.current:
            cur = self.current.evaluate()
            if self.current != cur:
                self.current = cur
                cur.moveto(userid)
                # cur.active()
                tmp.append((cur, 0))
                print("Moving into new state", cur.__class__.__name__,
                      cur.settings["Action"])
        for active, lastframe in self.active:
            frame = active.active(lastframe)
            if frame:
                tmp.append((active, frame))
        self.active = tmp


class Brain():
    """An executable brain object. Only one created per group it is used in"""
    def __init__(self, type, sim, newtree):
        self.newtree = functools.partial(newtree, self)
        self.sim = sim
        self.type = type
        self.neurons = {}
        self.outputs = []
        self.agvars = {}
        self.lvars = self.sim.lvars
        self.outvars = {}
        self.tags = {}
        self.isActiveSelection = False

    def reset(self):
        self.outvars = {"rx": 0, "ry": 0, "rz": 0,
                        "px": 0, "py": 0, "pz": 0}
        self.tags = self.sim.agents[self.currentuser].access["tags"]
        # self.tags = {}
        self.agvars = self.sim.agents[self.currentuser].agvars

    def execute(self, userid, statetree):
        # TODO could userid be replaced with self.currentuser?
        """Called for each time the agents needs to evaluate"""
        self.currentuser = userid
        self.isActiveSelection = bpy.context.active_object.name == userid
        self.reset()
        for name, var in self.lvars.items():
            var.setuser(userid)
        for neur in self.neurons.values():
            neur.newFrame()
        for out in self.outputs:
            self.neurons[out].evaluate()
        statetree.execute(userid)
