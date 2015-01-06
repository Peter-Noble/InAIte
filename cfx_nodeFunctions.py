from collections import OrderedDict
import math
from cfx_brainClasses import Neuron
from cfx_pythonEmbededInterpreter import Interpreter
import PySide
import copy

PCol = PySide.QtCore.Qt.GlobalColor


class LogicAND(Neuron):
    """returns the values multiplied together"""
    settings = OrderedDict()
    colour = PCol.darkGreen

    def core(self, keys, inps, settings, lvar, gvar):
        result = {}
        for k in keys:
            result[k] = 1
            for i in inps:
                result[k] *= i[k]
        return result


class LogicOR(Neuron):
    """returns the maximum value"""
    settings = OrderedDict()
    colour = PCol.darkGreen

    def core(self, keys, inps, settings, lvar, gvar):
        result = {}
        for k in keys:
            result[k] = max([i[k] for i in inps])
        return result


class LogicPYTHON(Neuron):
    """execute a python expression"""
    settings = OrderedDict([("Expression", {"type": "MLEdit",
                                            "value": "output = Noise.random"})])
    colour = PCol.darkCyan

    def core(self, keys, inps, settings, lvar, gvar):
        global Inter
        setup = copy.copy(lvar)
        setup["keys"] = keys
        setup["inps"] = inps
        setup["settings"] = settings
        Inter.setup(setup)
        Inter.enter(settings["Expression"]["value"])
        result = Inter.getoutput()
        if not isinstance(result, dict):
            result = {"None": result}
        return result


class LogicPRINT(Neuron):
    """print everything that is given to it"""
    settings = OrderedDict()
    colour = PCol.darkMagenta

    def core(self, keys, inps, settings, lvar, gvar):
        for k in keys:
            for i in inps:
                print("PRINT NODE >> ", k, i[k])
        return 1


class LogicMAP(Neuron):
    settings = OrderedDict([("Lower input", 1), ("Upper input", 2),
                            ("Lower output", 0), ("Upper output", 10)])
    colour = PCol.darkBlue

    def core(self, keys, inps, settings, lvar, gvar):
        result = {}
        if settings["Lower input"] != settings["Upper input"]:
            for k in keys:
                num = inps[0][k]
                # TODO currently takes the first input and ignores the rest
                li = settings["Lower input"]
                ui = settings["Upper input"]
                lo = settings["Lower output"]
                uo = settings["Upper output"]
                result[k] = ((uo - lo) / (ui - li)) * (num - li) + lo
        return result


class LogicOUTPUT(Neuron):
    settings = OrderedDict([("Output", ("ry", ("rx", "ry", "rz",
                                               "px", "py", "pz"))),
                            ("Multi input type", ("Average", ("Average", "Max")))
                            ])
    colour = PCol.darkRed

    def core(self, keys, inps, settings, lvar, gvar):
        vals = []
        for i in inps:
            vals += i.values()
        if settings["Multi input type"] == "Average":
            out = sum(vals)/len(vals)
        else:
            out = max(vals)
        self.brain.outvars[settings["Output"][0]] = out
        return inps


class LogicINPUT(Neuron):
    settings = OrderedDict([("Input", "Noise.random")])
    colour = PCol.cyan

    def core(self, keys, inps, settings, lvar, gvar):
        return eval(settings["Input"], lvar)

Inter = Interpreter()

logictypes = OrderedDict([
    ("AND", LogicAND),
    ("OR", LogicOR),
    ("PYTHON", LogicPYTHON),
    ("PRINT", LogicPRINT),
    ("MAP", LogicMAP),
    ("OUTPUT", LogicOUTPUT),
    ("INPUT", LogicINPUT)
])


class AnimSTD:
    settings = OrderedDict()

    def core(self):
        pass

animationtypes = {
    "STD": AnimSTD
}
