import bpy
from bpy.props import IntProperty, EnumProperty, CollectionProperty
from bpy.props import PointerProperty, BoolProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Panel, Operator

# =============== DATA START===============#

d = [('N', 'None', """{'edges': [], 'nodes': {}}"""),
     ('J', 'test', """{'nodes':
      {0: {'displayname': 'Node',
           'posx': -155.0,
           'type': 'LogicNode',
           'category': ('PYTHON', ['AND', 'OR', 'PYTHON', 'PRINT',
                                   'MAP', 'OUTPUT', 'INPUT']),
           'UID': 0,
           'frameparent': None,
           'settings': OrderedDict([('Expression',
                                     {'value': 'output = Noise.random/10',
                                      'type': 'MLEdit'})]),
           'posy': -110.0},
       1: {'displayname': 'Node',
           'posx': 21.25,0
           'type': 'LogicNode',
           'category': ('OUTPUT', ['AND', 'OR', 'PYTHON', 'PRINT',
                        'MAP', 'OUTPUT', 'INPUT']),
           'UID': 1,
           'frameparent': None,
           'settings': OrderedDict([('Output', ('rz', ('rx', 'ry', 'rz',
                                                       'px', 'py', 'pz'))),
                                    ('Multi input type',
                                     ('Average', ('Average', 'Max')))]),
           'posy': -107.5},
       2: {'displayname': 'Node',
           'posx': 56.25,
           'type': 'LogicNode',
           'category': ('OUTPUT', ['AND', 'OR', 'PYTHON', 'PRINT',
                                   'MAP', 'OUTPUT', 'INPUT']),
           'UID': 2,
           'frameparent': None,
           'settings': OrderedDict([('Output', ('py', ('rx', 'ry', 'rz',
                                                       'px', 'py', 'pz'))),
                                    ('Multi input type',
                                     ('Average', ('Average', 'Max')))]),
           'posy': 70.0},
       3: {'displayname': 'Node',
           'posx': -156.25,
           'type': 'LogicNode',
           'category': ('PYTHON', ['AND', 'OR', 'PYTHON', 'PRINT',
                                   'MAP', 'OUTPUT', 'INPUT']),
           'UID': 3,
           'frameparent': None,
           'settings': OrderedDict([('Expression', {'value': 'output = 0.05',
                                                    'type': 'MLEdit'})]),
           'posy': 65.0}
       },
         'edges': [{'source': 1, 'dest': 0},
                   {'source': 2, 'dest': 3}]
         }""".replace("\n", "").replace(" ", "")
      )]

default_slots = d


class brain_entry(PropertyGroup):
    """The data that is saved for each of the brain types"""
    identify = StringProperty(default="")
    dispname = StringProperty(default="")
    brain = StringProperty(default="")


def setCfxBrains():
    """loads the brains from the .blend or creates them if they don't already
    exist"""
    global cfx_brains
    bpy.types.Scene.cfx_brains = CollectionProperty(type=brain_entry)
    for b in default_slots:
        if b[0] not in [b.identify for b in bpy.context.scene.cfx_brains]:
            item = bpy.context.scene.cfx_brains.add()
            item.identify = b[0]
            item.dispname = b[1]
            item.brain = b[2]
    cfx_brains = bpy.context.scene.cfx_brains
    # print("Loaded brains", cfx_brains)


def cfx_brains_callback(scene, context):
    """Turns the brain data into a format that EnumProperty can take"""
    # print("Getting brains", cfx_brains)
    cfx_brains = bpy.context.scene.cfx_brains
    # TODO work out what's going on with cfx_brains and bpy.con...cfx_brains
    lis = [(x.identify, x.dispname, x.brain,) for x in cfx_brains]
    return lis


def updateagents(self, context):
    bpy.ops.scene.cfx_groups_populate()
    bpy.ops.scene.cfx_selected_populate()


class agent_entry(PropertyGroup):
    """The data structure for the agent entries"""
    type = EnumProperty(
        items=cfx_brains_callback,
        update=updateagents
    )
    group = IntProperty(update=updateagents)


class agents_collection(PropertyGroup):
    """cfx_agents, cfx_agents_selected"""
    coll = CollectionProperty(type=agent_entry)
    index = IntProperty()


class default_agents_type(PropertyGroup):
    """Properties that define how new objects will be assigned groups"""
    startType = EnumProperty(
        items=(
            ('Next', 'Next Free', ''),
            ('Set', 'Set to', '')
        )
    )
    contType = EnumProperty(
        items=(
            ('Same', 'All the same', ''),
            ('Inc', 'Increment next available', '')
        )
    )
    setno = IntProperty(min=1)


def setCfxAgents():
    """register cfx_agents type with blender"""
    PP = PointerProperty
    bpy.types.Scene.cfx_agents = PP(type=agents_collection)
    bpy.types.Scene.cfx_agents_selected = PP(type=agents_collection)
    bpy.types.Scene.cfx_agents_default = PP(type=default_agents_type)


def GroupChange(self, context):
    """callback for changing the type of one of the groups"""
    for agent in bpy.context.scene.cfx_agents.coll:
        if str(agent.group) == self.name:
            agent.type = self.type


class group_entry(PropertyGroup):
    """The data structure for the group entries"""
    type = EnumProperty(
        items=cfx_brains_callback,
        update=GroupChange
    )
    group = IntProperty(min=0)


class groups_collection(PropertyGroup):
    coll = CollectionProperty(type=group_entry)
    index = IntProperty()


def setCfxGroups():
    """register cfx_groups type with blender"""
    bpy.types.Scene.cfx_groups = PointerProperty(type=groups_collection)


def update_cfx_brains(brains):
    """passed to the GUI so that it can update the brain types"""

    """import subprocess
    def copy2clip(txt):
       cmd='echo '+txt.strip()+'|clip'
       return subprocess.check_call(cmd, shell=True)

    copy2clip(str(brains))"""

    cfx_brains = bpy.context.scene.cfx_brains
    idents = {}
    for x in cfx_brains:
        idents[x.identify] = x
    print("brains", brains)
    for bb in brains:
        if bb[0] in idents:
            print("Brain", bb[0], "modified")
            idents[bb[0]].dispname = bb[1]
            idents[bb[0]].brain = bb[2]
        else:
            print("New brain", bb[0], "added")
            item = cfx_brains.add()
            item.identify = bb[0]
            item.dispname = bb[1]
            item.brain = bb[2]
    setAllTypes()
    for g in bpy.context.scene.cfx_groups.coll:
        if g.type not in [x.identify for x in cfx_brains]:
            g.type = cfx_brains[0][1]
            # print(g, g.type)

registered = False


def setAllTypes():
    """register all types"""
    global registered
    if not registered:
        # bpy.utils.register_module(__name__)
        # I think this registers the SCENE_PT_crowdfx class...
        # ...or maybe all the classes in the file?
        bpy.utils.register_class(brain_entry)
        bpy.utils.register_class(agent_entry)
        bpy.utils.register_class(agents_collection)
        bpy.utils.register_class(default_agents_type)
        bpy.utils.register_class(group_entry)
        bpy.utils.register_class(groups_collection)
        registered = True
        setCfxBrains()
    setCfxGroups()
    setCfxAgents()


def unregisterAllTypes():
    # bpy.utils.unregister_module(__name__)
    # ...and this one unregisters the SCENE_PT_crowdfx
    bpy.utils.unregister_class(brain_entry)
    bpy.utils.unregister_class(agent_entry)
    bpy.utils.unregister_class(agents_collection)
    bpy.utils.unregister_class(default_agents_type)
    bpy.utils.unregister_class(group_entry)
    bpy.utils.unregister_class(groups_collection)
    del bpy.types.Scene.cfx_agents
    del bpy.types.Scene.cfx_groups
    del bpy.types.Scene.cfx_agents_selected
    del bpy.types.Scene.cfx_agents_default
    del bpy.types.Scene.cfx_brains

# =============== DATA END ===============#
