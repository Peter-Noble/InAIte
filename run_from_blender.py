for f in range(30):
    print("")

import bpy

import sys
path = r'''C:\Users\Peter\Documents\Hills road\Computing\A2\COMP4\CrowdFX'''
sys.path.append(path)

import imp

import cfx_main
imp.reload(cfx_main)
from cfx_main import bl_info, register, unregister
register()
