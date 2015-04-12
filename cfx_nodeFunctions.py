from collections import OrderedDict
import math
from . import cfx_brainClasses
from .cfx_brainClasses import Neuron, State
from . import cfx_pythonEmbededInterpreter
from .cfx_pythonEmbededInterpreter import Interpreter
import PySide
from PySide import QtGui, QtCore
import copy
import bpy

PCol = QtCore.Qt.GlobalColor

"""
class Logic{NAME}(Neuron):
    settings = OrderedDict([(key, value),
                            (key, value),
                            ...])
    # value can be any of the following:
    #   bool - Check box
    #   int - (±4294967296)
    #   float - (±4294967296)
    #   str - Single line string
    #   tuple - For dropdown boxes
    #       In form (default, (default, option1, option2...))
    #   dict - For custom custom types. val["type"] used to determine what to
    #       do with val["value"].
    #       val["type"] == "MLEdit" - str with newline characters allowed
    #       val["type"] == "Graph" - Graph for mapping a range of data to
                                    values between 0 and 1

    colour = QtGui.QColor(0, 0, 0)
    # The background colour of the node in the node editor (R, G, B)

    def core(self, inps, settings):
        # This function is the actual processing that the node represents

        # inps - list of all the inputs to this node which are ImpulseContainer
        # objects
        #    ImpulseContainer - Has 1 more more Impulse objects each of which
        #    has a key and a value
        # settings - The settings declared above. The first element
        # in each of the tuples is now the key to retrieve the second item.
"""


class LogicINPUT(Neuron):
    """Retrieve information from the scene or about the agent"""
    settings = OrderedDict([("Input", "Noise.random")])
    colour = QtGui.QColor(255, 0, 0)

    def core(self, inps, settings):
        lvars = copy.copy(self.brain.lvars)
        return eval(settings["Input"], lvars)


class LogicGRAPH(Neuron):
    """Return value 0 to 1 mapping from graph"""
    settings = OrderedDict([("Graph", {"type": "Graph",
                                       "value": ("linear",
                                                 [(0, 100),
                                                  (400, 100)
                                                  ])
                                       }),
                            ("Lower range", -1.0),
                            ("Upper range", 1.0),
                            ("Interpolation type", ("linear", ("linear",)))
                            ])

    colour = QtGui.QColor(255, 153, 0)

    def core(self, inps, settings):
        def linear(value):
            li = settings["Lower range"]
            ui = settings["Upper range"]
            if value <= li:
                num = li
            elif value >= ui:
                num = ui
            else:
                num = value
            # Num is value clipped into the range li<=num<=ui
            lo = 0
            uo = 400
            num = ((uo - lo) / (ui - li)) * (num - li) + lo
            raw = settings["Graph"]["value"][1]
            tmp = {}
            for r in raw:
                if r[0] in tmp:
                    tmp[r[0]] = max(tmp[r[0]], 100 - r[1])
                else:
                    tmp[r[0]] = 100 - r[1]
            vals = sorted(tmp.items(), key=lambda x: x[0])
            # vals is the list of points on the graph in x order and excluding
            # any that are directly under another point
            c = 0
            previous = vals[0]
            while vals[c][0] < num:
                previous = vals[c]
                c += 1
            current = vals[c]
            if current is previous:
                return current[1] / 100
            through = num - previous[0]
            ran = current[0] - previous[0]
            comp1 = ((through/ran) * current[1])
            comp2 = ((1 - through/ran) * previous[1])
            res = comp1 + comp2
            return res / 100

        if settings["Interpolation type"][0] == "linear":
            output = {}
            for into in inps:
                for i in into:
                    if i.key in output:
                        print("""LogicGRAPH data lost due to multiple inputs
                                 with the same key""")
                    else:
                        if settings["Interpolation type"][0] == "linear":
                            output[i.key] = linear(i.val)
                        # cubic bezier could also be an option here
        return output


class LogicAND(Neuron):
    """returns the values multiplied together"""
    settings = OrderedDict([("Single output", True)])
    colour = QtGui.QColor(204, 153, 0)

    def core(self, inps, settings):
        if settings["Single output"]:
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
    settings = OrderedDict([("Single output", True)])
    colour = QtGui.QColor(153, 204, 0)

    def core(self, inps, settings):
        if settings["Single output"]:
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
    settings = OrderedDict([("Tag", "default")
                            ])
    colour = QtGui.QColor(102, 255, 102)

    def core(self, inps, settings):
        if settings["Tag"] in self.brain.tags:
            return self.brain.tags[settings["Tag"]]
        else:
            return 0


class LogicSETTAG(Neuron):
    """If any of the inputs are above the Threshold level add or remove the
    Tag from the agents tags"""
    settings = OrderedDict([("Tag", "default"),
                            ("Use threshold", True),
                            ("Threshold", 0.5),
                            ("Action", ("Add", ("Add", "Remove"))),
                            ("Value", 5)
                            ])
    colour = QtGui.QColor(0, 153, 51)

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
        if settings["Use threshold"]:
            if condition:
                if settings["Action"][0] == "Add":
                    self.brain.tags[settings["Tag"]] = settings["Value"]
                else:
                    del self.brain.tags[settings["Tag"]]
        else:
            if settings["Action"][0] == "Add":
                self.brain.tags[settings["Tag"]] = total
            else:
                del self.brain.tags[settings["Tag"]]
        return settings["Threshold"]


class LogicVARIABLE(Neuron):
    """Set or retrieve (or both) an agent variable (0 if it doesn't exist)"""
    settings = OrderedDict([("Variable", "None")
                            ])
    colour = QtGui.QColor(0, 204, 153)

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
        return self.brain.agvars[settings["Variable"]]


class LogicMAP(Neuron):
    """Map the input from the input range to the output range
    (extrapolates outside of input range)"""
    settings = OrderedDict([("Lower input", 0.0), ("Upper input", 1.0),
                            ("Lower output", 0.0), ("Upper output", 2.0)])
    colour = QtGui.QColor(102, 255, 255)

    def core(self, inps, settings):
        result = {}
        if settings["Lower input"] != settings["Upper input"]:
            for into in inps:
                for i in into:
                    num = i.val
                    li = settings["Lower input"]
                    ui = settings["Upper input"]
                    lo = settings["Lower output"]
                    uo = settings["Upper output"]
                    result[i.key] = ((uo - lo) / (ui - li)) * (num - li) + lo
        return result


class LogicOUTPUT(Neuron):
    """Sets an agents output. (Has to be picked up in cfx_agents.Agents)"""
    settings = OrderedDict([("Output", ("ry", ("rx", "ry", "rz",
                                               "px", "py", "pz"))),
                            ("Multi input type",
                            ("Average", ("Average", "Max")))
                            ])
    colour = QtGui.QColor(0, 102, 153)

    def core(self, inps, settings):
        val = 0
        if settings["Multi input type"][0] == "Average":
            count = 0
            for into in inps:
                for i in into:
                    val += i.val
                    count += 1
            out = val/(max(1, count))
        elif settings["Multi input type"][0] == "Max":
            out = 0
            for into in inps:
                for i in into:
                    if abs(i.val) > abs(out):
                        out = i.val
        self.brain.outvars[settings["Output"][0]] = out
        return inps


class LogicEVENT(Neuron):
    """Check if an event is happening that frame"""
    settings = OrderedDict([("Event name", "default")])
    colour = QtGui.QColor(255, 153, 102)

    def core(self, inps, settings):
        events = bpy.context.scene.cfx_events.coll
        en = settings["Event name"]
        for e in events:
            if e.eventname == en:
                if e.time == bpy.context.scene.frame_current:
                    return 1
        return 0


class LogicPYTHON(Neuron):
    """execute a python expression"""
    settings = OrderedDict([("Expression", {"type": "MLEdit",
                                            "value": "output = Noise.random"})
                            ])
    colour = QtGui.QColor(0, 0, 0)

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
    settings = OrderedDict([("Label", "")])
    colour = QtGui.QColor(255, 255, 255)

    def core(self, inps, settings):
        selected = [o.name for o in bpy.context.selected_objects]
        if self.brain.currentuser in selected:
            for into in inps:
                for i in into:
                    print(settings["Label"], ">>", i.key, i.val)
        return 1

Inter = Interpreter()

logictypes = OrderedDict([
    ("INPUT", LogicINPUT),
    ("GRAPH", LogicGRAPH),
    ("AND", LogicAND),
    ("OR", LogicOR),
    ("QUERYTAG", LogicQUERYTAG),
    ("SETTAG", LogicSETTAG),
    ("VARIABLE", LogicVARIABLE),
    ("MAP", LogicMAP),
    ("OUTPUT", LogicOUTPUT),
    ("EVENT", LogicEVENT),
    ("PYTHON", LogicPYTHON),
    ("PRINT", LogicPRINT)
])


"""
class State{NAME}(State):
    settings = OrderedDict([("Action", ""),
                            ("Fade in", 5),
                            ("Fade out", 5)])
    colour = QtGui.QColor(128, 128, 128)

    def __ init__(self, tree):
        State.__init__(self, tree)

    def query(self):
        return 1
"""


class StateSTART(State):
    """Points to the first state for the agent to be in"""
    settings = OrderedDict([("Action", ""),
                            ("Fade in", 0),
                            ("Fade out", 0)])

    colour = QtGui.QColor(204, 102, 99)

    def __init__(self, tree):
        State.__init__(self, tree)
        self.start = True

    def query(self):
        return 0


class StateSTD(State):
    """The normal state in a state machine"""
    settings = OrderedDict([("Action", ""),
                            ("Trigger", "default"),
                            ("Fade in", 0),
                            ("Fade out", 0)])

    colour = QtGui.QColor(102, 153, 255)

    def __init__(self, tree):
        State.__init__(self, tree)

    def query(self):
        if self.settings["Trigger"] in self.tree.brain.tags:
            return self.tree.brain.tags[self.settings["Trigger"]]
        return 0


class StateTRANSITION(State):
    """This node queries the node its connected to and returns those results"""
    settings = OrderedDict([("Action", ""),
                            ("Fade in", 0),
                            ("Fade out", 0)])

    colour = QtGui.QColor(204, 204, 255)

    def __init__(self, tree):
        State.__init__(self, tree)

    def query(self):
        return self.connected[0].query()


class StateINTERRUPT(State):
    """Jump from anywhere to this node if a condition is met"""
    settings = OrderedDict([("Action", ""),
                            ("Trigger", "default"),
                            ("Theshold", 0.5),
                            ("Fade in", 0),
                            ("Fade out", 0),
                            ("Hard interrupt", True)])

    colour = QtGui.QColor(255, 204, 255)

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
