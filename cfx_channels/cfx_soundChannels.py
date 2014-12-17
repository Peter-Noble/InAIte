class Sound:
    """The object containing all of the sound channels"""
    def __init__(self):
        self.channels = []
			
    def newchannel(self, frequency):
        ch = Channel(frequency)
        if ch.frequency in dir(self):
            print("frequency must not be an attribute of this python object")
        else:
            setattr(self, ch.frequency, ch)
            self.channels.append(ch.frequency)

	
class Channel:
    """Holds a record of all objects that are emitting on a
    certain frequency"""
    def __init__(self, frequency):
        """
        :param frequency: The identifier for this channel
        :type frequency: String"""
        self.emitters = []
        self.frequency = frequency
		
    def register(self, objectid):
        """Add an object that emits sound"""
        self.emitters.append(objectid)
