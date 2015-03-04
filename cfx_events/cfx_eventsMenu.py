import bpy
import random
from bpy.props import IntProperty, EnumProperty, CollectionProperty
from bpy.props import PointerProperty, BoolProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Panel, Operator


class event_entry(PropertyGroup):
    """The data structure for the event entries"""
    eventname = StringProperty()
    time = IntProperty()
    index = IntProperty(min=0)


class events_collection(PropertyGroup):
    coll = CollectionProperty(type=event_entry)
    index = IntProperty()


class SCENE_OT_cfx_events_populate(Operator):
    bl_idname = "scene.cfx_events_populate"
    bl_label = "Populate cfx events list"

    def execute(self, context):
        item = context.scene.cfx_events.coll.add()
        return {'FINISHED'}


class SCENE_OT_event_remove(Operator):
    bl_idname = "scene.cfx_events_remove"
    bl_label = "Remove"

    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_events.coll) > s.cfx_events.index >= 0

    def execute(self, context):
        s = context.scene
        s.cfx_events.coll.remove(s.cfx_events.index)
        if s.cfx_events.index > 0:
            s.cfx_events.index -= 1
        return {'FINISHED'}


class SCENE_OT_event_move(Operator):
    bl_idname = "scene.cfx_events_move"
    bl_label = "Move"

    direction = EnumProperty(items=(
        ('UP', "Up", "Move up"),
        ('DOWN', "Down", "Move down"))
    )

    @classmethod
    def poll(cls, context):
        s = context.scene
        return len(s.cfx_events.coll) > s.cfx_events.index >= 0

    def execute(self, context):
        s = context.scene
        d = -1 if self.direction == 'UP' else 1
        new_index = (s.cfx_events.index + d) % len(s.cfx_events.coll)
        s.cfx_events.coll.move(s.cfx_events.index, new_index)
        s.cfx_events.index = new_index
        return {'FINISHED'}


class SCENE_UL_event(UIList):
    """for drawing each row"""
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # layout.label(text=str(item.name))
            layout.prop(item, "eventname", text="")
            layout.prop(item, "time", text="")
            # this draws each row in the list. Each line is a widget
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            # no idea when this is actually used


class SCENE_PT_event(Panel):
    """Creates CrowdFX Panel in the scene properties window"""
    bl_label = "CrowdFX - Events"
    bl_idname = "SCENE_PT_event"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        sce = context.scene

        row = layout.row()

        row.label("Events")

        row = layout.row()

        sce = bpy.context.scene

        row.template_list("SCENE_UL_event", "", sce.cfx_events,
                          "coll", sce.cfx_events, "index")

        col = row.column()
        sub = col.column(True)
        blid_ap = SCENE_OT_cfx_events_populate.bl_idname
        sub.operator(blid_ap, text="", icon="ZOOMIN")
        blid_ar = SCENE_OT_event_remove.bl_idname
        sub.operator(blid_ar, text="", icon="ZOOMOUT")

        sub = col.column(True)
        sub.separator()
        blid_am = SCENE_OT_event_move.bl_idname
        sub.operator(blid_am, text="", icon="TRIA_UP").direction = 'UP'
        sub.operator(blid_am, text="", icon="TRIA_DOWN").direction = 'DOWN'


def event_register():
    bpy.utils.register_class(event_entry)
    bpy.utils.register_class(SCENE_OT_cfx_events_populate)
    bpy.utils.register_class(SCENE_OT_event_remove)
    bpy.utils.register_class(SCENE_OT_event_move)
    bpy.utils.register_class(events_collection)
    bpy.utils.register_class(SCENE_UL_event)
    bpy.utils.register_class(SCENE_PT_event)
    bpy.types.Scene.cfx_events = PointerProperty(type=events_collection)


def event_unregister():
    bpy.utils.unregister_class(SCENE_UL_event)
    bpy.utils.unregister_class(SCENE_PT_event)
    bpy.utils.unregister_class(SCENE_OT_event_move)
    bpy.utils.unregister_class(SCENE_OT_event_remove)
    bpy.utils.unregister_class(SCENE_OT_cfx_events_populate)
    bpy.utils.unregister_class(events_collection)
    bpy.utils.unregister_class(event_entry)
