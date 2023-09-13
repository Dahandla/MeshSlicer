bl_info = {
    "name": "Mesh Slicer",
    "author": "Andre Dickinson",
    "version": (1, 1, 0),
    "blender": (3, 5, 0),
    "category": "Object",
    "description": "The Mesh Slicer addon allows users to slice 3D objects along a plane in Blender.",
    "warning": "",
    "wiki_url": "https://github.com/Dahandla/MeshSlicer/blob/main/README.md",
    "location": "View3D > Tools > Mesh Slicer",
    "Troubleshooting": "- Ensure that the object you're trying to slice is a mesh. The addon is designed to work with mesh objects.",
}

import bpy
import bmesh
import webbrowser
import mathutils

# Email functionality
def open_email_client(context):
    email_address = "saraintelai@gmail.com"
    subject = "Question about Mesh Slicer Addon"
    body = "Hello,\n\nI have a question about the Mesh Slicer addon..."
    webbrowser.open(f"mailto:{email_address}?subject={subject}&body={body}")

class WM_OT_OpenEmailClient(bpy.types.Operator):
    bl_idname = "wm.open_email_client"
    bl_label = "Open Email Client"

    def execute(self, context):
        open_email_client(context)
        return {'FINISHED'}

class MeshSlicerAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="If you have questions or issues, contact us:")
        layout.operator("wm.open_email_client", text="Send Email")
        
        # Add a button to open the documentation
        layout.operator("wm.url_open", text="Open Documentation").url = bl_info["wiki_url"]

def add_slicing_plane(context, location, rotation, scale_factor=1.1):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=location, rotation=rotation)
    plane = context.active_object
    bounding_box = context.object.dimensions
    plane.dimensions = [d * scale_factor for d in bounding_box]
    mat = bpy.data.materials.new(name="RedMaterial")
    mat.diffuse_color = (1, 0, 0, 1)
    plane.data.materials.append(mat)
    return plane

class OBJECT_OT_mesh_slicer(bpy.types.Operator):
    bl_idname = "object.mesh_slicer"
    bl_label = "Mesh Slicer"
    bl_options = {'REGISTER', 'UNDO'}

    slice_type: bpy.props.EnumProperty(
        name="Slice Type",
        items=[
            ("REMOVE_TOP", "Remove Top", ""),
            ("REMOVE_BOTTOM", "Remove Bottom", ""),
            ("SPLIT", "Split", ""),
            ("NO_SPLIT", "No Split", "")
        ],
        default='NO_SPLIT'
    )

    cap_holes: bpy.props.BoolProperty(
        name="Cap Holes",
        default=True
    )
    show_plane: bpy.props.BoolProperty(
        name="Show Plane",
        description="Toggle the visibility of the slicing plane after the operation",
        default=True
    )
    
    slicing_plane_location: bpy.props.FloatVectorProperty(
        name="Slicing Plane Location",
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'
    )

    slicing_plane_rotation: bpy.props.FloatVectorProperty(
        name="Slicing Plane Rotation",
        default=(0.0, 0.0, 0.0),
        subtype='EULER'
    )

    slicing_plane_scale_factor: bpy.props.FloatProperty(
        name="Slicing Plane Scale Factor",
        default=1.1
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "slice_type")
        layout.prop(self, "cap_holes")
        layout.prop(self, "show_plane")
        
        # Layout properties for the slicing plane
        layout.prop(self, "slicing_plane_location")
        layout.prop(self, "slicing_plane_rotation")
        layout.prop(self, "slicing_plane_scale_factor")
        layout.operator("object.mesh_slicer", text="Apply")

    def execute(self, context):
        obj = context.active_object
        slicing_plane = add_slicing_plane(context, self.slicing_plane_location, self.slicing_plane_rotation, self.slicing_plane_scale_factor)
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        plane_normal = mathutils.Vector((0, 0, 1))
        rot_matrix = mathutils.Euler(self.slicing_plane_rotation, 'XYZ').to_matrix()
        plane_normal.rotate(rot_matrix)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=self.slicing_plane_location, plane_no=plane_normal, 
                               clear_outer=self.slice_type in ['REMOVE_TOP'], 
                               clear_inner=self.slice_type in ['REMOVE_BOTTOM'])
        if self.cap_holes:
            bmesh.ops.edgenet_fill(bm, edges=bm.edges)
        bmesh.update_edit_mesh(obj.data, destructive=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        if not self.show_plane:
            slicing_plane.hide_viewport = True
        return {'FINISHED'}

class VIEW3D_PT_mesh_slicer_panel(bpy.types.Panel):
    bl_label = "Mesh Slicer"
    bl_idname = "VIEW3D_PT_mesh_slicer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_mesh_slicer.bl_idname)
        layout.operator(OBJECT_OT_clean_planes.bl_idname)

class OBJECT_OT_clean_planes(bpy.types.Operator):
    bl_idname = "object.clean_planes"
    bl_label = "Clean Planes"
    bl_description = "Delete all planes created by the slicer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        slicer_planes = [obj for obj in mesh_objects if 'Plane' in obj.name]
        for plane in slicer_planes:
            bpy.data.objects.remove(plane, do_unlink=True)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(WM_OT_OpenEmailClient)
    bpy.utils.register_class(MeshSlicerAddonPreferences)
    bpy.utils.register_class(OBJECT_OT_mesh_slicer)
    bpy.utils.register_class(VIEW3D_PT_mesh_slicer_panel)
    bpy.utils.register_class(OBJECT_OT_clean_planes)

def unregister():
    bpy.utils.unregister_class(WM_OT_OpenEmailClient)
    bpy.utils.unregister_class(MeshSlicerAddonPreferences)
    bpy.utils.unregister_class(OBJECT_OT_mesh_slicer)
    bpy.utils.unregister_class(VIEW3D_PT_mesh_slicer_panel)
    bpy.utils.unregister_class(OBJECT_OT_clean_planes)

if __name__ == "__main__":
    register()
