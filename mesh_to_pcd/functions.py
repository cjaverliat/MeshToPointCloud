import bpy
import pathlib
from dataclasses import dataclass

@dataclass
class PointCloud:
    positions: list
    colors: list
    vertex_groups_weights: dict[str, list[float]]

def get_socket_identifier(modifier, name):
    node_group = modifier.node_group
    sockets = node_group.interface.items_tree
    for socket_name, socket in sockets.items():
        if socket_name == name:
            return socket.identifier
    raise ValueError(f"Socket {name} not found.")

def set_socket_value(modifier, socket_name, value):
    socket_id = get_socket_identifier(modifier, socket_name)
    if socket_id is not None:
        modifier[socket_id] = value

def export_point_cloud(output_filepath, pcd: PointCloud):

    assert(len(pcd.positions) == len(pcd.colors))

    n_points = len(pcd.positions)

    with open(output_filepath, "w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {n_points}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("property uchar alpha\n")

        for group_name in pcd.vertex_groups_weights:
            f.write(f"property float _vertex_group_weight_{group_name}\n")

        f.write("end_header\n")
        for i in range(n_points):
            pos = pcd.positions[i].vector
            # Extract color in sRGB color space. Use .color to get in linear color space
            col = pcd.colors[i].color_srgb
            r = int(col[0] * 255)
            g = int(col[1] * 255)
            b = int(col[2] * 255)
            a = int(col[3] * 255)

            s = f"{pos[0]:.2f} {pos[1]:.2f} {pos[2]:.2f} {r} {g} {b} {a} "

            for group_name in pcd.vertex_groups_weights:
                w = pcd.vertex_groups_weights[group_name][i].value
                s += f"{w:.2f} "
            
            f.write(s + "\n")

def mesh_to_pcd(mesh, density_min, density_max, output_filepath, context):

    if mesh.type != "MESH":
        raise ValueError("Object is not a mesh.")

    generator = context.collection.objects.get("Generator")

    if generator is None:
        lib_filepath = pathlib.Path(__file__).parent / "generate_point_cloud.blend"

        if not lib_filepath.exists():
            raise FileNotFoundError(f"File {lib_filepath} not found.")

        with bpy.data.libraries.load(lib_filepath.absolute().as_posix(), link=True, assets_only=True) as (data_from, data_to):
            data_to.objects = ["Generator"]

        for obj in data_to.objects:
            context.collection.objects.link(obj)
            generator = obj
    
    try:
        if len(mesh.material_slots) == 0:
            raise ValueError(f"No material assigned to object {mesh.name}")

        material = mesh.material_slots[0].material
        base_color = material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"]

        modifier = generator.modifiers.get("GeometryNodes")
        material_texture = base_color.links[0].from_node.image if len(base_color.links) > 0 else None

        set_socket_value(modifier, "Object", mesh)
        set_socket_value(modifier, "Density Min", density_min)
        set_socket_value(modifier, "Density Max", density_max)
        set_socket_value(modifier, "Base Color", base_color.default_value)
        set_socket_value(modifier, "Texture", material_texture)
        set_socket_value(modifier, "Use Texture", material_texture is not None)

        depsgraph = context.evaluated_depsgraph_get()
        pcd_mesh_eval = generator.evaluated_get(depsgraph).to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

        pos_attr_data = pcd_mesh_eval.attributes['position'].data
        col_attr_data = pcd_mesh_eval.attributes['color'].data

        vertex_groups_name = [group.name for group in mesh.vertex_groups]
        vertex_groups_weights = {group_name: [] for group_name in vertex_groups_name}

        for attr_name, attr in pcd_mesh_eval.attributes.items():
            if attr_name in vertex_groups_name:
                vertex_groups_weights[attr_name] = attr.data

        pcd = PointCloud(positions=pos_attr_data, colors=col_attr_data, vertex_groups_weights=vertex_groups_weights)

        export_point_cloud(output_filepath, pcd)
    finally:
        bpy.data.objects.remove(generator, do_unlink=True)

