import bpy,bmesh
from math import *
from mathutils import *

m = bmesh.new()
m.from_mesh(bpy.context.active_object.data)
p = bpy.data.objects["Plane.001"]
for f in m.faces:
    for v in f.verts[0]:
        print(v)
    print(geometry.intersect_ray_tri(f.verts[0],f.verts[1],f.verts[2],Vector((0.0,0.0,1.0)),p.location))
        
#mathutils.geometry.intersect_ray_tri()

