from cfx_channels.cfx_masterChannels import MasterChannel as Mc
import math
import mathutils
import bpy

sce = bpy.context.scene
O = sce.objects


class Sound(Mc):
    """The object containing all of the sound channels"""
    def __init__(self, sim):
        Mc.__init__(self, sim)
        """All the different sound frequencies that were emitted last frame"""
        self.channels = {}

    def register(self, agent, frequency, val):
        print("registering new")
        if frequency in dir(self):
            print("""frequency must not be an attribute of this
                  python object""")
        else:
            if frequency not in self.channels:
                ch = Channel(frequency)
                self.channels[frequency] = ch
            self.channels[frequency].register(agent.id, val)
        print("Frequencies", [x.frequency for x in self.channels.values()])

    def retrieve(self, freq):
        """Dynamic properties"""
        return self.channel[freq]

    def newframe(self):
        self.channels = {}

    def setuser(self, userid):
        for chan in self.channels.values():
            chan.newuser(userid)
        Mc.setuser(self, userid)


class Channel:
    """Holds a record of all objects that are emitting on a
    certain frequency"""
    def __init__(self, frequency):
        """
        :param frequency: The identifier for this channel
        :type frequency: String"""
        self.emitters = {}
        self.frequency = frequency
        """Temporary storage which is reset after each agents has used it"""
        self.store = {}

    def register(self, objectid, val):
        """Add an object that emits sound"""
        self.emitters[objectid] = val

    def newuser(self, userid):
        self.userid = userid
        self.store = {}

    def calculate(self):
        ag = O[self.userid]
        canhear = {}
        for emitterid, val in self.emitters.items():
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
                canhear[emitterid] = (changez, changex, dist/val)
        self.store = {}

    @property
    def rz(self):
        """Return the horizontal angle of sound emitting agents"""
        if not self.store:
            self.calculate()
        r = {k: v[0] for k, v in self.store.items()}
        if r:
            return r

    @property
    def rx(self):
        """Return the vertical angle of sound emitting agents"""
        if not self.store:
            self.calculate()
        r = {k: v[1] for k, v in self.store.items()}
        if r:
            return r

    @property
    def db(self):
        """Return the volume of sound emitting agents"""
        if not self.store:
            self.calculate()
        r = {k: v[2] for k, v in self.store.items()}
        if r:
            return r
