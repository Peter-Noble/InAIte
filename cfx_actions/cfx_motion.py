import bpy


class action:
    def __init__(self, name, actionname):
        A = bpy.data.actions
        sce = bpy.context.scene

        self.name = name
        self.actionname = actionname

        self.motiondata = {}

        if actionname in A:
            self.action = A[self.actionname]
            arange = self.action.frame_range
            self.length = arange[1] - arange[0] + 1
            for c in range(6):
                datapath = self.action.fcurves[c].data_path
                if datapath not in self.motiondata:
                    self.motiondata[datapath] = []
                self.motiondata[datapath].append([])
                for frame in range(int(arange[0]), int(arange[1])+1):
                    self.motiondata[datapath].append([])
                    val = self.action.fcurves[c].evaluate(frame)
                    self.motiondata[datapath][-1].append(val)
            # This assumes animation data for 3xlocation and 3xrotation
        else:
            self.action = None  # So that other code can do - if action.action
            self.length = 0


def getmotions():
    sce = bpy.context.scene
    result = {}
    for m in sce.cfx_actions.coll:
        result[m.name] = action(m.name, m.action)
    return result


# D.actions['Cube.007Action'].fcurves[4].evaluate(10)
