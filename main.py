import bpy
import random
from bpy.props import IntProperty, EnumProperty, CollectionProperty, PointerProperty, BoolProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Panel, Operator


#=============== DATA START===============#

#This will eventually contain references to the brain objects
#When this needs updating append to this list and then call the setCfx... functions
cfx_brains = (
            ('N', "None", ""),
            ('A', "Option A", ""),  
            ('B', "Option B", ""),
            ('G', "Ground", "")
            )
#The data structure for the agent entries
def updateagents(self, context):
    bpy.ops.scene.cfx_groups_populate()
    bpy.ops.scene.cfx_selected_populate()

class agent_entry(PropertyGroup):
    type = EnumProperty(
        items=(cfx_brains),
        update=updateagents
    )
    group = IntProperty(update=updateagents)

#cfx_agents, cfx_agents_selected
class agents_collection(PropertyGroup):
    coll = CollectionProperty(type=agent_entry)
    index = IntProperty()

class default_agents_type(PropertyGroup):
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

#register cfx_agents type with blender
def setCfxAgents():
    bpy.types.Scene.cfx_agents = PointerProperty(type=agents_collection)
    bpy.types.Scene.cfx_agents_selected = PointerProperty(type=agents_collection)
    bpy.types.Scene.cfx_agents_default = PointerProperty(type=default_agents_type)

#callback for changing the type of one of the groups
def GroupChange(self, context):
    for agent in bpy.context.scene.cfx_agents.coll:
        if str(agent.group) == self.name:
            agent.type = self.type

#The data structure for the group entries
class group_entry(PropertyGroup):
    type = EnumProperty (
        items = (cfx_brains),
        update = GroupChange
    )
    group = IntProperty(min=0)

class groups_collection(PropertyGroup):
    coll = CollectionProperty(type=group_entry)
    index = IntProperty()

#register cfx_groups type with blender
def setCfxGroups():
    bpy.types.Scene.cfx_groups = PointerProperty(type=groups_collection)



#register all types
def setAllTypes():
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
    
   #needs list clean up adding




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
        
        print("start")
        
        for i in bpy.context.scene.cfx_agents.coll:
            if self.group.index<len(self.group.coll):
                if i.group==int(self.group.coll[self.group.index].name):
                    item = context.scene.cfx_agents_selected.coll.add()
                    item.name = i.name
                    print(i.name)
        return {'FINISHED'}
    
#=============== SELECTED LIST END ===============#

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

def register():
    bpy.utils.register_module(__name__)#I think this registers the SCENE_PT_crowdfx class... or maybe all the classes in the file?
    #PointerProperty can be reassigned during execution
    setAllTypes()

def unregister():
    bpy.utils.unregister_module(__name__)#...and this one unregisters the SCENE_PT_crowdfx
    del bpy.types.Scene.cfx_agents
    del bpy.types.Scene.cfx_groups
    del bpy.types.Scene.cfx_agents_selected
    del bpy.types.Scene.cfx_agents_default

if __name__ == "__main__":
    register()




