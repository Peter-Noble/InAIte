from collections import OrderedDict
import math
from cfx_brainClasses import Neuron


class LogicAND(Neuron):
    """returns the values multiplied together"""
    settings = OrderedDict()

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

    def core(self, keys, inps, settings, lvar, gvar):
        result = {}
        for k in keys:
            result[k] = max([i[k] for i in inps])
        return result


class LogicPYTHON(Neuron):
    """execute a python expression"""
    settings = OrderedDict([("Expression", "1")])

    def core(self, keys, inps, settings, lvar, gvar):
        result = {"None": eval(settings["Expression"])}
        return result


class LogicPRINT(Neuron):
    """print everything that is given to it"""
    settings = OrderedDict()

    def core(self, keys, inps, settings, lvar, gvar):
        for k in keys:
            for i in inps:
                print("Print node", k, i, i[k])
        return 1


class LogicMAP(Neuron):
    settings = OrderedDict([("Lower input", 1), ("Upper input", 2), ("Lower output", 0), ("Upper output", 10)])

    def core(self, keys, inps, settings, lvar, gvar):
        result = {}
        if settings["Lower input"] != settings["Upper input"]:
            for k in keys:
                num = inps[0][k]  # TODO this currently only takes the first input and ignores the rest
                li = settings["Lower input"]
                ui = settings["Upper input"]
                lo = settings["Lower output"]
                uo = settings["Upper output"]
                result[k] = ((uo - lo) / (ui - li)) * (num - li) + lo
        return result


class LogicOUTPUT(Neuron):
    settings = OrderedDict([("Multi input type", ("Average", ("Max", "Average")))])

    def core(self, keys, inps, settings, lvar, gvar):
        # TODO output some stuff to the Blender scene
        result = {}
        for k in keys:
            result[k] = [inps[ke] for ke in keys]
        return result


logictypes = OrderedDict([
    ("AND", LogicAND),
    ("OR", LogicOR),
    ("PYTHON", LogicPYTHON),
    ("PRINT", LogicPRINT),
    ("MAP", LogicMAP),
    ("OUTPUT", LogicOUTPUT)
])


class AnimSTD:
    settings = OrderedDict()

    def core(self):
        pass

animationtypes = {
    "STD": AnimSTD
}