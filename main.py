import bpy
import random
from bpy.props import IntProperty, EnumProperty, CollectionProperty, PointerProperty, BoolProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Panel, Operator

import sys
sys.path.append(r'''C:\Users\Peter\Documents\Hills road\Computing\A2\COMP4\CrowdFX''')

from cfx_simulate import Simulation
from cfx_gui import runui

bl_info = {
	"name": "CFX",
	"description": "Simulate crowds of agents in Blender!",
	"author": "Peter Noble",
	"version": (1,0),
	"blender": (2,73,0),
	"location": "Properties > Scene",
	"category": "Development"
}

#=============== DATA START===============#

cfx_brains = []

def loadbrains():
    """loads the brains from the .blend or creates them if they don't already exist"""
    global cfx_brains
    if "cfx_brains" not in bpy.context.scene:
        bpy.types.Scene.cfx_brains = [
            ('N', 'None', "{'edges': [], 'nodes': {}}"),
            ('J', 'test', "{'nodes': {0: {'displayname': 'Node', 'posx': -155.0, 'type': 'LogicNode', 'category': ('PYTHON', ['AND', 'OR', 'PYTHON', 'PRINT', 'MAP', 'OUTPUT', 'INPUT']), 'UID': 0, 'frameparent': None, 'settings': OrderedDict([('Expression', {'value': 'output = Noise.random/10', 'type': 'MLEdit'})]), 'posy': -110.0}, 1: {'displayname': 'Node', 'posx': 21.25, 'type': 'LogicNode', 'category': ('OUTPUT', ['AND', 'OR', 'PYTHON', 'PRINT', 'MAP', 'OUTPUT', 'INPUT']), 'UID': 1, 'frameparent': None, 'settings': OrderedDict([('Output', ('rz', ('rx', 'ry', 'rz', 'px', 'py', 'pz'))), ('Multi input type', ('Average', ('Average', 'Max')))]), 'posy': -107.5}, 2: {'displayname': 'Node', 'posx': 56.25, 'type': 'LogicNode', 'category': ('OUTPUT', ['AND', 'OR', 'PYTHON', 'PRINT', 'MAP', 'OUTPUT', 'INPUT']), 'UID': 2, 'frameparent': None, 'settings': OrderedDict([('Output', ('py', ('rx', 'ry', 'rz', 'px', 'py', 'pz'))), ('Multi input type', ('Average', ('Average', 'Max')))]), 'posy': 70.0}, 3: {'displayname': 'Node', 'posx': -156.25, 'type': 'LogicNode', 'category': ('PYTHON', ['AND', 'OR', 'PYTHON', 'PRINT', 'MAP', 'OUTPUT', 'INPUT']), 'UID': 3, 'frameparent': None, 'settings': OrderedDict([('Expression', {'value': 'output = 0.05', 'type': 'MLEdit'})]), 'posy': 65.0}}, 'edges': [{'source': 1, 'dest': 0}, {'source': 2, 'dest': 3}]}")
            ]
    cfx_brains = bpy.context.scene.cfx_brains
    print("Loaded brains", cfx_brains)

def cfx_brains_callback(scene, context):
    """Very useful for debugging purposes"""
    #print("Getting brains", cfx_brains)
    return cfx_brains

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
        items = (
            ('Next','Next Free',''),
            ('Set','Set to','')
        )
    )
    contType = EnumProperty(
        items = (
            ('Same','All the same',''),
            ('Inc','Increment next available','')
        )
    )
    setno = IntProperty(min=1)

def setCfxAgents():
    """register cfx_agents type with blender"""
    bpy.types.Scene.cfx_agents = PointerProperty(type=agents_collection)
    bpy.types.Scene.cfx_agents_selected = PointerProperty(type=agents_collection)
    bpy.types.Scene.cfx_agents_default = PointerProperty(type=default_agents_type)

def GroupChange(self, context):
    """callback for changing the type of one of the groups"""
    for agent in bpy.context.scene.cfx_agents.coll:
        if str(agent.group) == self.name:
            agent.type = self.type

class group_entry(PropertyGroup):
    """The data structure for the group entries"""
    type = EnumProperty (
        items = cfx_brains_callback,
        update = GroupChange
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
    import subprocess
    def copy2clip(txt):
       cmd='echo '+txt.strip()+'|clip'
       return subprocess.check_call(cmd, shell=True)
    
    copy2clip(str(brains))

    global cfx_brains
    cfx_brains = [('N', 'None', "{'edges': [], 'nodes': {}}")]
    for bb in brains:
        cfx_brains.append(bb)
    setAllTypes()
    for g in bpy.context.scene.cfx_groups.coll:
        if g.type not in [x[0] for x in cfx_brains]:
            g.type = cfx_brains[0][1]
            print(g, g.type)
    print([x[0] for x in cfx_brains])

def setAllTypes():
    """register all types"""
    setCfxGroups()
    setCfxAgents()
    
#=============== DATA END ===============#

#=============== GROUPS LIST START ===============#

class SCENE_UL_group(UIList):
    """for drawing each row"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=str(item.name))
            layout.prop(item, "type", text="")
            #this draws each row in the list. Each line is a widget
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            #no idea when this is actually used


class SCENE_OT_group_populate(Operator):
    bl_idname = "scene.cfx_groups_populate"
    bl_label = "Populate group list"
    
    def execute(self, context):
        groups = []
        toRemove = []
        for f in range(len(bpy.context.scene.cfx_groups.coll)):
            name=bpy.context.scene.cfx_groups.coll[f].name
            if (name not in groups) and (name in [str(x.group) for x in bpy.context.scene.cfx_agents.coll]):
                groups.append(bpy.context.scene.cfx_groups.coll[f].name)
            else:
                toRemove.append(f)
        for f in reversed(toRemove):
            print(len(bpy.context.scene.cfx_groups.coll))
            bpy.context.scene.cfx_groups.coll.remove(f)
        for agent in bpy.context.scene.cfx_agents.coll:
            if str(agent.group) not in groups:
                groups.append(str(agent.group))
                item = context.scene.cfx_groups.coll.add()
                item.name = str(agent.group)
                item.type = 'N'
        return {'FINISHED'}
    
   # TODO  needs list clean up adding


class SCENE_OT_group_remove(Operator):
    """NOT USED NEEDS REMOVING ONCE THE POPULATE KEEPS THE LIST CLEAR"""
    bl_idname = "scene.cfx_groups_remove"
    bl_label = "Remove"
    
    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_groups.coll) > s.cfx_groups.index >= 0
    
    def execute(self, context):
        s = context.scene
        s.cfx_groups.coll.remove(s.cfx_groups.index)
        if s.cfx_groups.index > 0:
            s.cfx_groups.index -= 1
        return {'FINISHED'}
    
class SCENE_OT_group_move(Operator):
    """NEEDS TO BE REMOVED ONCE POPULATE IS WORKING"""
    bl_idname = "scene.cfx_groups_move"
    bl_label = "Move"

    direction = EnumProperty(items=(
        ('UP', "Up", "Move up"),
        ('DOWN', "Down", "Move down"))
    )
    
    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_groups.coll) > s.cfx_groups.index >= 0

    def execute(self, context):
        s = context.scene
        d = -1 if self.direction == 'UP' else 1
        new_index = (s.cfx_groups.index + d) % len(s.cfx_groups.coll)
        s.cfx_groups.coll.move(s.cfx_groups.index, new_index)
        s.cfx_groups.index = new_index
        return {'FINISHED'}
    
#=============== GROUPS LIST END ===============#

#=============== AGENTS LIST START ===============#

class SCENE_UL_agents(UIList):
    """for drawing each row"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            ic = 'OBJECT_DATA' if item.name in bpy.context.scene.objects else 'ERROR'
            layout.prop_search(item, "name", bpy.data, "objects")
            layout.prop(item, "group", text="")
            layout.label(text=item.type)
            #this draws each row in the list. Each line is a widget
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            #no idea when this is actually used
    
    
class SCENE_OT_cfx_agents_populate(Operator):
    bl_idname = "scene.cfx_agents_populate"
    bl_label = "Populate cfx agents list"
    
    def findNext(self):
        g = [x.group for x in bpy.context.scene.cfx_agents.coll]
        i = 1
        while True:
            if i not in g:
                return i
            else:
                i+=1
            
    def execute(self, context):
        ag = [x.name for x in bpy.context.scene.cfx_agents.coll]
        
        if bpy.context.scene.cfx_agents_default.startType=="Next":
            group = self.findNext()
        else:
            group = bpy.context.scene.cfx_agents_default.setno
        
        for i in bpy.context.selected_objects:
            if i.name not in ag:
                item = context.scene.cfx_agents.coll.add()
                item.name = i.name
                item.group = group
                if bpy.context.scene.cfx_agents_default.contType=="Inc":
                    if bpy.context.scene.cfx_agents_default.startType=="Next":
                        group = self.findNext()
                    else:
                        bpy.context.scene.cfx_agents_default.setno+=1
                        group = bpy.context.scene.cfx_agents_default.setno
                print("cfx", cfx_brains)
                item.type = 'N'
        bpy.ops.scene.cfx_groups_populate()
        return {'FINISHED'}
    
class SCENE_OT_agent_remove(Operator):
    bl_idname = "scene.cfx_agents_remove"
    bl_label = "Remove"
    
    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_agents.coll) > s.cfx_agents.index >= 0
    
    def execute(self, context):
        s = context.scene
        s.cfx_agents.coll.remove(s.cfx_agents.index)
        if s.cfx_agents.index > 0:
            s.cfx_agents.index -= 1
        return {'FINISHED'}
    
class SCENE_OT_agent_move(Operator):
    bl_idname = "scene.cfx_agents_move"
    bl_label = "Move"

    direction = EnumProperty(items=(
        ('UP', "Up", "Move up"),
        ('DOWN', "Down", "Move down"))
    )
    
    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_agents.coll) > s.cfx_agents.index >= 0

    def execute(self, context):
        s = context.scene
        d = -1 if self.direction == 'UP' else 1
        new_index = (s.cfx_agents.index + d) % len(s.cfx_agents.coll)
        s.cfx_agents.coll.move(s.cfx_agents.index, new_index)
        s.cfx_agents.index = new_index
        return {'FINISHED'}
    

#=============== AGENTS LIST END ===============#

#=============== SELECTED LIST START ===============#

class SCENE_UL_selected(UIList):
    """for drawing each row"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            ic = 'OBJECT_DATA' if item.name in bpy.context.scene.objects else 'ERROR'
            layout.prop(item, "name", text="", emboss=False, icon=ic)
            #layout.label(text=str(item.group))
            #layout.prop(item, "group")
            #layout.label(text=item.type)
            #this draws each row in the list. Each line is a widget
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            #no idea when this is actually used

        
class SCENE_OT_cfx_selected_populate(Operator):
    bl_idname = "scene.cfx_selected_populate"
    bl_label = "See group"
    
    def execute(self, context):
        self.group = bpy.context.scene.cfx_groups
        self.group_selected = bpy.context.scene.cfx_agents_selected
        self.group_selected.coll.clear()
        
        for i in bpy.context.scene.cfx_agents.coll:
            if self.group.index<len(self.group.coll):
                if i.group==int(self.group.coll[self.group.index].name):
                    item = context.scene.cfx_agents_selected.coll.add()
                    item.name = i.name
        return {'FINISHED'}
    
#=============== SELECTED LIST END ===============#

#=============== SIMULATION START ===============#


class SCENE_OT_cfx_startui(Operator):
    bl_idname = "scene.cfx_startui"
    bl_label = "start UI"
    
    def execute(self, context):
        runui(update_cfx_brains)
        return {'FINISHED'}


class SCENE_OT_cfx_start(Operator):
    bl_idname = "scene.cfx_start"
    bl_label = "Start simulation"
    
    def execute(self, context):
        sim = Simulation()
        for ag in bpy.context.scene.cfx_agents.coll:
            sim.newagent(ag.name)
        sim.startframehandler()
        return {'FINISHED'}

#=============== SIMULATION END ===============#


class SCENE_PT_crowdfx(Panel):
    """Creates CrowdFX Panel in the scene properties window"""
    bl_label = "CrowdFX"
    bl_idname = "SCENE_PT_crowdfx"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        sce = context.scene

        row = layout.row()
        row.template_list("SCENE_UL_group", "", sce.cfx_groups, "coll", sce.cfx_groups, "index")
            
        col = row.column()
        sub = col.column(True)
        sub.operator(SCENE_OT_group_populate.bl_idname, text="", icon="ZOOMIN")
        
        
        sub = col.column(True)
        sub.separator()
        sub.operator(SCENE_OT_group_move.bl_idname, text="", icon="TRIA_UP").direction = 'UP'
        sub.operator(SCENE_OT_group_move.bl_idname, text="", icon="TRIA_DOWN").direction = 'DOWN'
        sub.separator()
        sub.operator(SCENE_OT_cfx_selected_populate.bl_idname, text="", icon="PLUS")
        
        #####
        
        layout.label(text="Selected Agents")
        layout.template_list("SCENE_UL_selected", "", sce.cfx_agents_selected, "coll", sce.cfx_agents_selected, "index")
        
        #####
        
        layout.label(text="All agents:")
        row = layout.row()
        row.template_list("SCENE_UL_agents", "", sce.cfx_agents, "coll", sce.cfx_agents, "index")
            
        col = row.column()
        sub = col.column(True)
        sub.operator(SCENE_OT_cfx_agents_populate.bl_idname, text="", icon="ZOOMIN")
        sub.operator(SCENE_OT_agent_remove.bl_idname, text="", icon="ZOOMOUT")
        
        sub = col.column(True)
        sub.separator()
        sub.operator(SCENE_OT_agent_move.bl_idname, text="", icon="TRIA_UP").direction = 'UP'
        sub.operator(SCENE_OT_agent_move.bl_idname, text="", icon="TRIA_DOWN").direction = 'DOWN'

        default = bpy.context.scene.cfx_agents_default
        layout.label(text="Default agents group:")

        row = layout.row()
        row.prop(default, "startType", expand=True)
        row.prop(default, "setno", text="")
        
        row = layout.row()
        row.prop(default, "contType", expand=True)
        
        row = layout.row()
        row.operator(SCENE_OT_cfx_startui.bl_idname)
        row.operator(SCENE_OT_cfx_start.bl_idname)

def register():
    bpy.utils.register_module(__name__)#I think this registers the SCENE_PT_crowdfx class... or maybe all the classes in the file?
    loadbrains()
    setAllTypes()

def unregister():
    bpy.utils.unregister_module(__name__)#...and this one unregisters the SCENE_PT_crowdfx
    del bpy.types.Scene.cfx_agents
    del bpy.types.Scene.cfx_groups
    del bpy.types.Scene.cfx_agents_selected
    del bpy.types.Scene.cfx_agents_default

if __name__ == "__main__":
    register()