from collections import OrderedDict
import math


class LogicAND:
    """returns the values multiplied together"""
    settings = OrderedDict()

    @staticmethod
    def core(keys, inps, settings):
        result = {}
        for k in keys:
            result[k] = 1
            for i in inps:
                result[k] *= i[k]
        return result


class LogicOR:
    """returns the maximum value"""
    settings = OrderedDict()

    @staticmethod
    def core(keys, inps, settings):
        result = {}
        for k in keys:
            result[k] = max([i[k] for i in inps])
        return result


class LogicPYTHON:
    """execute a python expression"""
    settings = OrderedDict([("Expression", "1")])

    @staticmethod
    def core(keys, inps, settings):
        result = {}
        result["None"] = eval(settings["Expression"])
        return result


class LogicPRINT:
    """print everything that is given to it"""
    settings = OrderedDict()

    @staticmethod
    def core(keys, inps, settings):
        for k in keys:
            for i in inps:
                print("Print node", k, i, i[k])
        return 1


logictypes = {
    "AND": LogicAND,
    "OR": LogicOR,
    "PYTHON": LogicPYTHON,
    "PRINT": LogicPRINT
}


class AnimSTD:
    settings = OrderedDict()

    @staticmethod
    def core():
        pass

animationtypes = {
    "STD": AnimSTD
}