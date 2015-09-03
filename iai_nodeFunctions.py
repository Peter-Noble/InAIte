from collections import OrderedDict
import math
from . import iai_brainClasses
from .iai_brainClasses import Neuron, State
from . import iai_pythonEmbededInterpreter
from .iai_pythonEmbededInterpreter import Interpreter
import copy
import bpy


"""
Instructions of creating new neurons need redoing
"""


class LogicINPUT(Neuron):
    """Retrieve information from the scene or about the agent"""

    def core(self, inps, settings):
        lvars = copy.copy(self.brain.lvars)
        lvars["math"] = math
        return eval(settings["Input"], lvars)


class LogicGRAPH(Neuron):
    """Return value 0 to 1 mapping from graph"""

    def core(self, inps, settings):
        def linear(value):
            lz = settings["LowerZero"]
            lo = settings["LowerOne"]
            uo = settings["UpperOne"]
            uz = settings["UpperZero"]

            if value < lz:
                return 0
            elif value < lo:
                return (value - lz) / (lo - lz)
            elif value < uo:
                return 1
            elif value < uz:
                return (value - uo) / (uz - uo)
            else:
                return 0

        def RBF(value):
            u = settings["RBFMiddle"]
            TPP = settings["RBFTenPP"]

            a = math.log(0.1) / (TPP**2)
            return math.e**(a*(value-u)**2)

        output = {}
        for into in inps:
            for i in into:
                if i.key in output:
                    print("""LogicGRAPH data lost due to multiple inputs
                             with the same key""")
                else:
                    if settings["CurveType"] == "RBF":
                        output[i.key] = RBF(i.val)
                    elif settings["CurveType"] == "RANGE":
                        output[i.key] = linear(i.val)
                    # cubic bezier could also be an option here (1/2 sided)
        return output


class LogicAND(Neuron):
    """returns the values multiplied together"""

    def core(self, inps, settings):
        if settings["SingleOutput"]:
            total = 1
            for into in inps:
                for i in into:
                    total *= i.val
            return {"None": total}
        else:
            results = {}
            for into in inps:
                for i in into:
                    if i.key in results:
                        results[i.key] *= i.val
                    else:
                        results[i.key] = i.val
            return results


class LogicOR(Neuron):
    """If any of the values are high return a high value
    1 - ((1-a) * (1-b) * (1-c)...)"""

    def core(self, inps, settings):
        if settings["SingleOutput"]:
            total = 1
            for into in inps:
                for i in [i.val for i in into]:
                    total *= (1-i)
            return 1-total
        else:
            results = {}
            for into in inps:
                for i in into:
                    if i.key in results:
                        results[i.key] *= (1-i.val)
                    else:
                        results[i.key] = (1-i.val)
            results.update((k, 1-v) for k, v in results.items())
            return results


class LogicQUERYTAG(Neuron):
    """Return the value of Tag (normally 1) or else 0"""

    def core(self, inps, settings):
        if settings["Tag"] in self.brain.tags:
            return self.brain.tags[settings["Tag"]]
        else:
            return 0


class LogicSETTAG(Neuron):
    """If any of the inputs are above the Threshold level add or remove the
    Tag from the agents tags"""

    def core(self, inps, settings):
        condition = False
        total = 0
        count = 0
        for into in inps:
            for i in into:
                    if i.val > settings["Threshold"]:
                        condition = True
                    total += i.val
                    count += 1
        if settings["UseThreshold"]:
            if condition:
                if settings["Action"] == "ADD":
                    self.brain.tags[settings["Tag"]] = 1
                else:
                    if settings["Tag"] in self.brain.tags:
                        del self.brain.tags[settings["Tag"]]
        else:
            if settings["Action"] == "ADD":
                self.brain.tags[settings["Tag"]] = total
            else:
                if settings["Tag"] in self.brain.tags:
                    del self.brain.tags[settings["Tag"]]
        return settings["Threshold"]


class LogicVARIABLE(Neuron):
    """Set or retrieve (or both) an agent variable (0 if it doesn't exist)"""

    def core(self, inps, settings):
        count = 0
        for into in inps:
            for i in into:
                self.brain.agvars[settings["Variable"]] += i.val
                count += 1
        if count:
            self.brain.agvars[settings["Variable"]] /= count
        if settings["Variable"] in self.brain.agvars:
            out = self.brain.agvars[settings["Variable"]]
        else:
            out = 0
        # TODO Doesn't work
        return self.brain.agvars[settings["Variable"]]


class LogicMAP(Neuron):
    """Map the input from the input range to the output range
    (extrapolates outside of input range)"""

    def core(self, inps, settings):
        result = {}
        if settings["LowerInput"] != settings["UpperInput"]:
            for into in inps:
                for i in into:
                    num = i.val
                    li = settings["LowerInput"]
                    ui = settings["UpperInput"]
                    lo = settings["LowerOutput"]
                    uo = settings["UpperOutput"]
                    result[i.key] = ((uo - lo) / (ui - li)) * (num - li) + lo
        return result


class LogicOUTPUT(Neuron):
    """Sets an agents output. (Has to be picked up in iai_agents.Agents)"""

    def core(self, inps, settings):
        val = 0
        if settings["MultiInputType"] == "AVERAGE":
            count = 0
            for into in inps:
                for i in into:
                    val += i.val
                    count += 1
            out = val/(max(1, count))
        elif settings["MultiInputType"] == "MAX":
            out = 0
            for into in inps:
                for i in into:
                    if abs(i.val) > abs(out):
                        out = i.val
        elif settings["MultiInputType"] == "SIZEAVERAGE":
            """Takes a weighed average of the inputs where smaller values have
            less of an impact on the final result"""
            Sm = 0
            SmSquared = 0
            for into in inps:
                for i in into:
                    print("Val:", i.val)
                    Sm += i.val
                    SmSquared += i.val * abs(i.val)  # To retain sign
            print(Sm, SmSquared)
            if Sm == 0:
                out = 0
            else:
                out = SmSquared / Sm
            print("out", out)
        self.brain.outvars[settings["Output"]] = out
        # TODO doesn't output anything


class LogicEVENT(Neuron):
    """Check if an event is happening that frame"""

    def core(self, inps, settings):
        events = bpy.context.scene.iai_events.coll
        en = settings["EventName"]
        for e in events:
            if e.eventname == en:
                result = 1
                if e.category == "Time" or e.category == "Time+Volume":
                    if e.time == bpy.context.scene.frame_current:
                        result *= 1
                    else:
                        result *= 0
                if e.category == "Volume" or e.category == "Time+Volume":
                    if result:
                        pt = bpy.data.objects[self.brain.currentuser].location
                        l = bpy.data.objects[e.volume].location
                        d = bpy.data.objects[e.volume].dimensions

                        ins = False
                        if l.x-(d.x/2) <= pt.x <= l.x+(d.x/2):
                            if l.y-(d.y/2) <= pt.y <= l.y+(d.y/2):
                                if l.z-(d.z/2) <= pt.z <= l.z+(d.z/2):
                                    ins = True
                        if ins:
                            result *= 1
                        else:
                            result *= 0
                return result
        return 0


class LogicPYTHON(Neuron):
    """execute a python expression"""

    def core(self, inps, settings):
        global Inter
        setup = copy.copy(self.brain.lvars)
        setup["inps"] = inps
        setup["settings"] = settings
        Inter.setup(setup)
        Inter.enter(settings["Expression"]["value"])
        result = Inter.getoutput()
        return result


class LogicPRINT(Neuron):
    """print everything that is given to it"""

    def core(self, inps, settings):
        selected = [o.name for o in bpy.context.selected_objects]
        if self.brain.currentuser in selected:
            for into in inps:
                for i in into:
                    print(settings["Label"], ">>", i.key, i.val)
        return 0

Inter = Interpreter()

logictypes = OrderedDict([
    ("InputNode", LogicINPUT),
    ("GraphNode", LogicGRAPH),
    ("AndNode", LogicAND),
    ("OrNode", LogicOR),
    ("QueryTagNode", LogicQUERYTAG),
    ("SetTagNode", LogicSETTAG),
    ("VariableNode", LogicVARIABLE),
    ("MapNode", LogicMAP),
    ("OutputNode", LogicOUTPUT),
    ("EventNode", LogicEVENT),
    ("PythonNode", LogicPYTHON),
    ("PrintNode", LogicPRINT)
])


"""
State trees need redoing
"""


class StateSTART(State):
    """Points to the first state for the agent to be in"""

    def __init__(self, tree):
        State.__init__(self, tree)
        self.start = True

    def query(self):
        return 0


class StateSTD(State):
    """The normal state in a state machine"""

    def __init__(self, tree):
        State.__init__(self, tree)

    def query(self):
        if self.settings["Trigger"] in self.tree.brain.tags:
            return self.tree.brain.tags[self.settings["Trigger"]]
        return 0


class StateTRANSITION(State):
    """This node queries the node its connected to and returns those results"""

    def __init__(self, tree):
        State.__init__(self, tree)

    def query(self):
        return self.connected[0].query()


class StateINTERRUPT(State):
    """Jump from anywhere to this node if a condition is met"""

    def __init__(self, tree):
        State.__init__(self, tree)
        self.interrupt = True

    def query(self):
        if self.settings["Trigger"] in self.tree.brain.tags:
            val = self.tree.brain.tags[self.settings["Trigger"]]
            if val > self.settings["Theshold"]:
                return val
        return 0

statetypes = OrderedDict([
    ("START", StateSTART),
    ("STD", StateSTD),
    ("TRANSITION", StateTRANSITION),
    ("INTERRUPT", StateINTERRUPT)
])
