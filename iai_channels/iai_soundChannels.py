from .iai_masterChannels import MasterChannel as Mc
import math
import mathutils
Vector = mathutils.Vector

if __name__ != "__main__":
    import bpy

    O = bpy.context.scene.objects
else:
    import unittest

    from .iai_masterChannels import Wrapper as wr

    class FakeObject():
        """Impersonate bpy.context.scene.objects[n]"""
        def __init__(self, location, rotation):
            self.location = mathutils.Vector(location)
            self.rotation_euler = mathutils.Euler(rotation)

    class FakeAgent():
        """Impersonate Simulation.agents[n]"""
        def __init__(self, bid):
            self.id = bid

    class FakeSimulation():
        """Impersonate the Simulation object"""
        def __init__(self):
            self.framelast = 1

    class Test(unittest.TestCase):
        def setUp(self):
            global O
            # Impersonate bpy.context.scene.objects
            # These are the objects that can be used to emit and hear sounds
            O = {"OB1": FakeObject([0, 0, 0], [0, 0, 0]),
                 "OB2": FakeObject([1, 0, 0], [0, 0, 0]),
                 "OB3": FakeObject([0, 1, 0], [0, 0, 0]),
                 "OB4": FakeObject([0, -1, 0], [0, 0, 0]),
                 "OB5": FakeObject([-0.1, -1, 0], [0, 0, 0])}

            self.FSim = FakeSimulation()

            self.sound = wr(Sound(self.FSim))

        def testOne(self):
            """Some simple test cases"""
            self.sound.register(FakeAgent("OB1", "A", 1))
            self.sound.register(FakeAgent("OB2", "A", 1))
            self.sound.register(FakeAgent("OB3", "A", 1))

            self.sound.setuser("OB1")
            self.assertEqual(self.sound.A.rz, {"OB2": 0.5,
                                               "OB3": 0})
            self.assertEqual(self.sound.A.db, {"OB2": 0,
                                               "OB3": 0})

        def testBoundryRotations(self):
            """Testing the extremes of the rotation"""
            self.sound.register(FakeAgent("OB1", "A", 1))
            self.sound.register(FakeAgent("OB4", "A", 1))
            self.sound.register(FakeAgent("OB5", "A", 1))

            self.sound.setuser("OB1")
            self.assertEqual(self.sound.A.rz["OB4"], 1)
            self.assertTrue(-1 < self.sound.A.rz["OB5"] < -0.75)

        def tearDown(self):
            self.sound.newFrame()

    # Run unit test
    unittest.main()


class Sound(Mc):
    """The object containing all of the sound channels"""
    def __init__(self, sim):
        Mc.__init__(self, sim)
        # All the different sound frequencies that were emitted last frame
        self.channels = {}

    def register(self, agent, frequency, val):
        """Adds an object that is emitting a sound"""
        if frequency in dir(self):
            print("""frequency must not be an attribute of this
                  python object""")
        else:
            if frequency not in self.channels:
                ch = Channel(frequency, self.sim)
                self.channels[frequency] = ch
            self.channels[frequency].register(agent.id, val)

    def retrieve(self, freq):
        """Dynamic properties"""
        if (freq in self.channels):
            return self.channels[freq]
        else:
            return EmptyChannel()
            # TODO this is really hacky...

    def newframe(self):
        self.channels = {}

    def setuser(self, userid):
        for chan in self.channels.values():
            chan.newuser(userid)
        Mc.setuser(self, userid)


class EmptyChannel():
    def __getattr__(self, attr):
        if attr == "pred":
            return self
        else:
            return {"None": 0}


class Channel:
    """Holds a record of all objects that are emitting on a
    certain frequency"""
    def __init__(self, frequency, sim):
        """
        :param frequency: The identifier for this channel
        :type frequency: String"""
        self.sim = sim

        self.emitters = {}
        self.frequency = frequency
        # Temporary storage which is reset after each agents has used it
        self.store = {}
        self.storePrediction = {}

        self.predictNext = False

    def register(self, objectid, val):
        """Add an object that emits sound"""
        self.emitters[objectid] = val

    def newuser(self, userid):
        self.userid = userid
        self.store = {}
        self.storePrediction = {}

    def calculate(self):
        """Called the first time an agent uses this frequency"""
        ag = O[self.userid]
        for emitterid, val in self.emitters.items():
            if emitterid != self.userid:
                to = O[emitterid]

                difx = to.location.x - ag.location.x
                dify = to.location.y - ag.location.y
                difz = to.location.z - ag.location.z
                dist = math.sqrt(difx**2 + dify**2 + difz**2)
                if dist <= val:
                    target = to.location - ag.location

                    z = mathutils.Matrix.Rotation(ag.rotation_euler[2], 4, 'Z')
                    y = mathutils.Matrix.Rotation(ag.rotation_euler[1], 4, 'Y')
                    x = mathutils.Matrix.Rotation(ag.rotation_euler[0], 4, 'X')

                    rotation = x * y * z
                    relative = target * rotation

                    changez = math.atan2(relative[0], relative[1])/math.pi
                    changex = math.atan2(relative[2], relative[1])/math.pi
                    self.store[emitterid] = (changez, changex, 1-(dist/val), 1)
                    # (z rot, x rot, dist proportion, time until prediction)

    def calculatePrediction(self):
        """Called the first time an agent uses this frequency"""
        ag = O[self.userid]
        agSim = self.sim.agents[self.userid]
        for emitterid, val in self.emitters.items():
            if emitterid != self.userid:
                to = O[emitterid]
                toSim = self.sim.agents[emitterid]

                p1 = mathutils.Vector((agSim.apx, agSim.apy, agSim.apz))
                p2 = mathutils.Vector((toSim.apx, toSim.apy, toSim.apz))

                d1 = mathutils.Vector(agSim.globalVelocity)
                d2 = mathutils.Vector(toSim.globalVelocity)

                # O["Cube.Pointer"].location = p1 + (d1 * 2)
                # O["Cube.001.Pointer"].location = p2 + (d2 * 2)

                a = d1.dot(d1)
                b = d1.dot(d2)
                e = d2.dot(d2)

                d = a*e - b*b

                if (d != 0):  # If the two lines are not parallel.
                    r = p1 - p2
                    c = d1.dot(r)
                    f = d2.dot(r)

                    s = (b*f - c*e) / d
                    t = (a*f - b*c) / d
                    # t*d2 == closest point
                    # s*d2 == point 2 is at when 1 is at closest approach
                    pd1 = p1 + (s*d1)
                    pd2 = p2 + (s*d2)
                    dist = (pd1 - pd2).length
                else:
                    dist = float("inf")

                # pd1 and pd2 are the positions the agents will be when they
                #  make their closest approach
                if dist <= val:
                    target = pd2 - pd1

                    z = mathutils.Matrix.Rotation(ag.rotation_euler[2], 4, 'Z')
                    y = mathutils.Matrix.Rotation(ag.rotation_euler[1], 4, 'Y')
                    x = mathutils.Matrix.Rotation(ag.rotation_euler[0], 4, 'X')

                    rotation = x * y * z
                    relative = target * rotation

                    changez = math.atan2(relative[0], relative[1])/math.pi
                    changex = math.atan2(relative[2], relative[1])/math.pi
                    if (s < 1) or (t < 1):
                        cert = 0
                    else:
                        # This equation results in overflow errors
                        # cert = math.log(2+abs(c)+adjust)*(math.e**(-2**(abs(c)+adjust)**2))
                        if s > 32:
                            c = 1
                        else:
                            c = s / 32
                        cert = (1 - ((-(c**3)/3 + (c**2)/2) * 6))**2
                    self.storePrediction[emitterid] = (changez, changex, 1-(dist/val), cert)
                    # (z rot, x rot, dist proportion, time until prediction)

    @property
    def pred(self):
        self.predictNext = True
        return self

    @property
    def rz(self):
        """Return the horizontal angle of sound emitting agents"""
        pre = self.predictNext
        self.predictNext = False
        if pre:
            if not self.storePrediction:
                self.calculatePrediction()
            r = {k: v[0] for k, v in self.storePrediction.items()}
        else:
            if not self.store:
                self.calculate()
            r = {k: v[0] for k, v in self.store.items()}
        if r:
            return r

    @property
    def rx(self):
        """Return the vertical angle of sound emitting agents"""
        pre = self.predictNext
        self.predictNext = False
        if pre:
            if not self.storePrediction:
                self.calculatePrediction()
            r = {k: v[1] for k, v in self.storePrediction.items()}
        else:
            if not self.store:
                self.calculate()
            r = {k: v[1] for k, v in self.store.items()}
        if r:
            return r

    @property
    def dist(self):
        """Return the distance to the sound emitting agents 0-1"""
        pre = self.predictNext
        self.predictNext = False
        if pre:
            if not self.storePrediction:
                self.calculatePrediction()
            r = {k: v[2] for k, v in self.storePrediction.items()}
        else:
            if not self.store:
                self.calculate()
            r = {k: v[2] for k, v in self.store.items()}
        if r:
            return r

    @property
    def db(self):
        """Return the volume (dist^2) of sound emitting agents"""
        pre = self.predictNext
        self.predictNext = False
        if pre:
            if not self.storePrediction:
                self.calculatePrediction()
            r = {k: v[2]**2 for k, v in self.storePrediction.items()}
        else:
            if not self.store:
                self.calculate()
            r = {k: v[2]**2 for k, v in self.store.items()}
        if r:
            return r

    @property
    def certainty(self):
        """Return the certainty of a prediction 0-1"""
        pre = self.predictNext
        self.predictNext = False
        if pre:
            if not self.storePrediction:
                self.calculatePrediction()
            r = {k: v[3] for k, v in self.storePrediction.items()}
        else:
            if not self.store:
                self.calculate()
            r = {k: v[3] for k, v in self.store.items()}
        if r:
            return r
