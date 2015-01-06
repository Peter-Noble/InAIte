import code


class Interpreter(code.InteractiveConsole):
    def __init__(self, *args):
        code.InteractiveConsole.__init__(self, *args)

    def enter(self, codesource):
        source = self.preprocess(codesource)
        self.runcode(source)

    @staticmethod
    def preprocess(codesource):
        """This could be used to add macros"""
        return codesource

    def setup(self, localvars):
        self.locals = {'__name__': '__console__', '__doc__': None}
        for v in localvars:
            self.locals[v] = localvars[v]

    def getoutput(self):
        if "output" in self.locals:
            return self.locals["output"]
        else:
            print("Script must have out output")


if __name__ == "__main__":
    console = Interpreter()
    console.enter("a = 1\noutput = a + 1")
    print(console.getoutput())