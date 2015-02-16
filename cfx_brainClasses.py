import cfx_channels as chan
import PySide
import random
import functools
import bpy

sce = bpy.context.scene


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

    def moveto(self, userid):
        """Called when the current state moves to this node"""
        self.currentframe = 0
        act = self.settings["Action"]  # STRING
        if act in self.tree.brain.sim.actions:
            actionobj = self.tree.brain.sim.actions[act]  # from cfx_motion.py
            obj = sce.objects[userid]  # bpy object
            tr = obj.animation_data.nla_tracks.new()  # NLA track
            action = actionobj.action  # bpy action
            strip = tr.strips.new("", sce.frame_current, action)
            strip.extrapolation = 'HOLD_FORWARD'
            strip.use_auto_blend = True
            # This needs replacing with fade values from the nodes
            self.length = actionobj.length

    def active(self):
        self.currentframe += 1
        if self.currentframe < self.length:
            fr = self.currentframe
            action = self.tree.brain.sim.actions[self.settings["Action"]]
            if "rotation_euler" in action.motiondata:
                rot = action.motiondata["rotation_euler"]
                self.tree.brain.outvars["rx"] += rot[0][fr] - rot[0][fr - 1]
                self.tree.brain.outvars["ry"] += rot[1][fr] - rot[1][fr - 1]
                self.tree.brain.outvars["rz"] += rot[2][fr] - rot[2][fr - 1]
            if "location" in action.motiondata:
                loc = action.motiondata["location"]
                self.tree.brain.outvars["px"] += loc[0][fr] - loc[0][fr - 1]
                self.tree.brain.outvars["py"] += loc[1][fr] - loc[1][fr - 1]
                self.tree.brain.outvars["pz"] += loc[2][fr] - loc[2][fr - 1]
            return True
        else:
            return False

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
            # self.currentframe += 1
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
    def __init__(self, brain):
        self.brain = brain
        self.interupts = []
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
                tmp.append(cur)
                # print("Moving into new state", cur.__class__.__name__)
        for active in self.active:
            if active.active():
                tmp.append(active)
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

    def reset(self):
        self.outvars = {"rx": 0, "ry": 0, "rz": 0,
                        "px": 0, "py": 0, "pz": 0}
        self.tags = self.sim.agents[self.currentuser].access["tags"]
        self.agvars = self.sim.agents[self.currentuser].agvars

    def execute(self, userid, statetree):
        """Called for each time the agents needs to evaluate"""
        self.currentuser = userid
        self.reset()
        for name, var in self.lvars.items():
            var.setuser(userid)
        for out in self.outputs:
            self.neurons[out].evaluate()
        statetree.execute(userid)
