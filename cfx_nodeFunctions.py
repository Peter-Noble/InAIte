from collections import OrderedDict
import math
from cfx_brainClasses import Neuron, State
from cfx_pythonEmbededInterpreter import Interpreter
import PySide
from PySide import QtGui, QtCore
import copy

PCol = QtCore.Qt.GlobalColor

"""
class Logic{NAME}(Neuron):
    settings = OrderedDict([(key, value),
                            (key, value),
                            ...])
    # value can be any of the following:
    #   bool - Check box
    #   int - (±99999)
    #   float - (±99999)
    #   str - Single line string
    #   tuple - For dropdown boxes
    #       In form (default, (default, option1, option2...))
    #   dict - For custom custom types. val["type"] used to determine what to
    #       do with val["value"].
    #       val["type"] == "MLEdit" - str with newline characters allowed
    #       val["type"] == "Graph" - Graph for mapping a range of data to
                                    values between 0 and 1

    colour = QtGui.QColor(PCol.green)
    # The background colour of the node in the node editor

    def core(self, inps, settings):
        # This function is the actual processing that the node represents

        # inps - list of all the inputs to this node which are ImpulseContainer
        # objects
        #    ImpulseContainer - Has 1 more more Impulse objects each of which
        #    has a key and a value
        # settings - The settings declared above. The first element
        # in each of the tuples is now the key to retrieve the second item.
"""


class LogicAND(Neuron):
    """returns the values multiplied together"""
    settings = OrderedDict([("Single output", True)])
    colour = QtGui.QColor(PCol.darkGreen)

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
    """returns the maximum value"""
    settings = OrderedDict([("Single output", True)])
    colour = QtGui.QColor(PCol.darkGreen)

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


class LogicPYTHON(Neuron):
    """execute a python expression"""
    settings = OrderedDict([("Expression", {"type": "MLEdit",
                                            "value": "output = Noise.random"})
                            ])
    colour = QtGui.QColor(PCol.darkCyan)

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
    colour = QtGui.QColor(PCol.darkMagenta)

    def core(self, inps, settings):
        for into in inps:
            for i in into:
                print("PRINT NODE", settings["Label"], ">>", i.key, i.val)
        return 1


class LogicMAP(Neuron):
    """Map the input from the input range to the output range
    (extrapolates outside of input range)"""
    settings = OrderedDict([("Lower input", 1.0), ("Upper input", 2.0),
                            ("Lower output", 0.0), ("Upper output", 10.0)])
    colour = QtGui.QColor(PCol.darkBlue)

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
    colour = QtGui.QColor(PCol.darkRed)

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


class LogicINPUT(Neuron):
    """Retrieve information from the scene or about the agent"""
    settings = OrderedDict([("Input", "Noise.random")])
    colour = QtGui.QColor(PCol.cyan)

    def core(self, inps, settings):
        lvars = copy.copy(self.brain.lvars)
        return eval(settings["Input"], lvars)


class LogicSETTAG(Neuron):
    """If any of the inputs are above the Threshold level add or remove the
    Tag from the agents tags"""
    settings = OrderedDict([("Tag", "default"),
                            ("Threshold", 0.5),
                            ("Action", ("Add", ("Add", "Remove"))),
                            ("Value", 5)
                            ])
    colour = QtGui.QColor(PCol.darkYellow)

    def core(self, inps, settings):
        condition = False
        for into in inps:
            for i in into:
                    if i.val > settings["Threshold"]:
                        condition = True
        if condition:
            if settings["Action"][0] == "Add":
                self.brain.tags[settings["Tag"]] = settings["Value"]
            else:
                del self.brain.tags[settings["Tag"]]
        return settings["Threshold"]


class LogicQUERYTAG(Neuron):
    """Return the value of Tag (normally 1) or else 0"""
    settings = OrderedDict([("Tag", "default")
                            ])
    colour = QtGui.QColor(PCol.yellow)

    def core(self, inps, settings):
        if settings["Tag"] in self.brain.tags:
            return self.brains.tags[settings["Tag"]]
        else:
            return 0


class LogicVARIABLE(Neuron):
    """Set or retrieve (or both) an agent variable (0 if it doesn't exist)"""
    settings = OrderedDict([("Variable", "None")
                            ])
    colour = QtGui.QColor(PCol.magenta)

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
                            ("Interpolation type", ("linear", ("linear")))
                            ])

    colour = QtGui.QColor(204, 0, 102)

    def core(self, inps, settings):
        def linear(value, points):
            pass  # TODO  do some magic here
        if settings["Interpolation type"][0] == "linear":
            output = {}
            for into in inps:
                for i in into:
                    if i.key in output:
                        print("""LogicGRAPH data lots due to multiple inputs
                                 with the same key""")
                    else:
                        if settings["Interpolation type"][0] == "linear":
                            output[i.key] = linear(i.val)

Inter = Interpreter()

logictypes = OrderedDict([
    ("AND", LogicAND),
    ("OR", LogicOR),
    ("PYTHON", LogicPYTHON),
    ("PRINT", LogicPRINT),
    ("MAP", LogicMAP),
    ("OUTPUT", LogicOUTPUT),
    ("INPUT", LogicINPUT),
    ("SETTAG", LogicSETTAG),
    ("QUERYTAG", LogicQUERYTAG),
    ("VARIABLE", LogicVARIABLE),
    ("GRAPH", LogicGRAPH)
])


class StateSTART(State):
    settings = OrderedDict([("Default out", "default")])

    colour = QtGui.QColor(255, 255, 153)

    start = True

    def core(self, settings):
        pass


class StateSTD(State):
    settings = OrderedDict([("Default out", "default")])

    colour = QtGui.QColor(0, 0, 0)

    def core(self, settings):
        pass


class StateINTERUPT(State):
    settings = OrderedDict([("Hard interupt", True),
                            ("Default out", "default")])

    colour = QtGui.QColor(255, 51, 0)

    interupt = True

    def core(self, settings):
        pass

    def evaluateinterupt(self):
        """Called for all interupt nodes in the preprocessing step"""
        pass


class StateTRANSITION(State):
    settings = OrderedDict([("Default out", "default")])

    colour = QtGui.QColor(255, 128, 0)

    def core(self, settings):
        pass


statetypes = OrderedDict([
    ("STD", StateSTD),
    ("INTERUPT", StateINTERUPT),
    ("START", StateSTART),
    ("TRANSITION", StateTRANSITION)
])
