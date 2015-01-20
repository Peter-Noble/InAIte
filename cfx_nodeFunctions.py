from collections import OrderedDict
import math
from cfx_brainClasses import Neuron
from cfx_pythonEmbededInterpreter import Interpreter
import PySide
import copy

PCol = PySide.QtCore.Qt.GlobalColor


class LogicAND(Neuron):
    """returns the values multiplied together"""
    settings = OrderedDict([("Single output", True)])
    colour = PCol.darkGreen

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
    colour = PCol.darkGreen

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
    colour = PCol.darkCyan

    def core(self, inps, settings):
        global Inter
        setup = copy.copy(self.brain.lvars)
        setup["keys"] = keys
        setup["inps"] = inps
        setup["settings"] = settings
        Inter.setup(setup)
        Inter.enter(settings["Expression"]["value"])
        result = Inter.getoutput()
        return result


class LogicPRINT(Neuron):
    """print everything that is given to it"""
    settings = OrderedDict()
    colour = PCol.darkMagenta

    def core(self, inps, settings):
        for into in inps:
            for i in into:
                print("PRINT NODE >> ", i)
        return 1


class LogicMAP(Neuron):
    """Map the input from the input range to the output range
    (extrapolates outside of input range)"""
    settings = OrderedDict([("Lower input", 1), ("Upper input", 2),
                            ("Lower output", 0), ("Upper output", 10)])
    colour = PCol.darkBlue

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
    colour = PCol.darkRed

    def core(self, inps, settings):
        val = 0
        if settings["Multi input type"] == "Average":
            count = 0
            for into in inps:
                for i in inps:
                    val += i.val
                    count += 1
            out = val/(max(1, count))
        elif settings["Multi input type"] == "Max":
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
    colour = PCol.cyan

    def core(self, inps, settings):
        lvars = copy.copy(self.brain.lvars)
        return eval(settings["Input"], lvars)


class LogicSETTAG(Neuron):
    """If any of the inputs are above the Threshold level add or remove the
    Tag from the agents tags"""
    settings = OrderedDict([("Tag", "default"),
                            ("Threshold", 0.5),
                            ("Action", ("Add", ("Add", "Remove")))
                            ])
    colour = PCol.darkYellow

    def core(self, inps, settings):
        condition = False
        for into in inps:
            for i in into:
                    if i.val > settings["Threshold"]:
                        condition = True
        if condition:
            if settings["Action"][0] == "Add":
                self.brain.tags[settings["Tag"]] = 1
            else:
                del self.brain.tags[settings["Tag"]]
        return settings["Threshold"]


class LogicQUERYTAG(Neuron):
    """Return the value of Tag (normally 1) or else 0"""
    settings = OrderedDict([("Tag", "default")
                            ])
    colour = PCol.yellow

    def core(self, inps, settings):
        if settings["Tag"] in self.brain.tags:
            return self.brains.tags[settings["Tag"]]
        else:
            return 0


class LogicVARIABLE(Neuron):
    """Set or retrieve (or both) an agent variable (0 if it doesn't exist)"""
    settings = OrderedDict([("Variable", "None")
                            ])
    colour = PCol.magenta

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
    ("VARIABLE", LogicVARIABLE)
])


class AnimSTD:
    settings = OrderedDict()

    def core(self):
        pass

animationtypes = OrderedDict([
    ("STD", AnimSTD)
])
