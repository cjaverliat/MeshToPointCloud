import bpy
from .operators import register as operators_register, unregister as operators_unregister

bl_info = {
    "name": "Mesh to Point Cloud",
    "blender": (4, 1, 0),
    "category": "Object",
}

def register():
    operators_register()

def unregister():
    operators_unregister()

if __name__ == "__main__":
    register()