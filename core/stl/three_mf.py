from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

import numpy as np
import trimesh


MAX_ARCHIVE_MEMBERS = 512
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_MODEL_XML_BYTES = 25 * 1024 * 1024

UNIT_TO_MM = {
    "micron": 0.001,
    "millimeter": 1.0,
    "centimeter": 10.0,
    "inch": 25.4,
    "foot": 304.8,
    "meter": 1000.0,
}


@dataclass
class ThreeMFModel:
    mesh: trimesh.Trimesh
    source_unit: str
    object_count: int
    build_item_count: int


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _parse_transform(raw: str | None, scale_to_mm: float) -> np.ndarray:
    if not raw:
        return np.eye(4)

    try:
        values = [float(value) for value in raw.split()]
    except ValueError as exc:
        raise ValueError("the 3MF contains an invalid object transform") from exc

    if len(values) != 12 or not np.isfinite(values).all():
        raise ValueError("the 3MF contains an invalid object transform")

    return np.array(
        [
            [values[0], values[3], values[6], values[9] * scale_to_mm],
            [values[1], values[4], values[7], values[10] * scale_to_mm],
            [values[2], values[5], values[8], values[11] * scale_to_mm],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def _mesh_from_object(element: ElementTree.Element, scale_to_mm: float) -> trimesh.Trimesh | None:
    meshes = _children(element, "mesh")
    if not meshes:
        return None

    vertices_elements = _children(meshes[0], "vertices")
    triangles_elements = _children(meshes[0], "triangles")
    if not vertices_elements or not triangles_elements:
        raise ValueError("the 3MF mesh is missing vertices or triangles")

    try:
        vertices = [
            (
                float(vertex.attrib["x"]) * scale_to_mm,
                float(vertex.attrib["y"]) * scale_to_mm,
                float(vertex.attrib["z"]) * scale_to_mm,
            )
            for vertex in _children(vertices_elements[0], "vertex")
        ]
        triangles = [
            (
                int(triangle.attrib["v1"]),
                int(triangle.attrib["v2"]),
                int(triangle.attrib["v3"]),
            )
            for triangle in _children(triangles_elements[0], "triangle")
        ]
    except (KeyError, ValueError) as exc:
        raise ValueError("the 3MF contains invalid mesh coordinates or triangle indexes") from exc

    if not vertices or not triangles:
        raise ValueError("the 3MF mesh does not contain any triangle geometry")

    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(triangles), process=False)
    if mesh.faces.max() >= len(mesh.vertices) or mesh.faces.min() < 0:
        raise ValueError("the 3MF contains a triangle index outside its vertex list")
    return mesh


def _read_model_xml(path: str) -> bytes:
    try:
        with ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise ValueError("the 3MF archive contains too many files")

            total_size = sum(member.file_size for member in members)
            if total_size > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError("the 3MF archive expands beyond the safe analysis limit")

            model_members = [
                member
                for member in members
                if not member.is_dir()
                and member.filename.lower().endswith(".model")
                and Path(member.filename).parts
                and Path(member.filename).parts[0].lower() == "3d"
            ]
            if not model_members:
                raise ValueError("the 3MF archive does not contain a 3D model")

            model_member = model_members[0]
            if model_member.file_size > MAX_MODEL_XML_BYTES:
                raise ValueError("the 3MF model XML exceeds the safe analysis limit")
            return archive.read(model_member)
    except BadZipFile as exc:
        raise ValueError("the file is not a readable 3MF archive") from exc


def load_3mf_mesh(path: str) -> ThreeMFModel:
    xml_bytes = _read_model_xml(path)
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise ValueError("the 3MF model XML is malformed") from exc

    if _local_name(root.tag) != "model":
        raise ValueError("the 3MF model XML has an invalid root element")

    source_unit = root.attrib.get("unit", "millimeter").lower()
    scale_to_mm = UNIT_TO_MM.get(source_unit)
    if scale_to_mm is None:
        raise ValueError(f"the 3MF uses an unsupported unit: {source_unit}")

    resources = next(iter(_children(root, "resources")), None)
    if resources is None:
        raise ValueError("the 3MF model does not contain resources")

    object_elements = {
        element.attrib["id"]: element
        for element in _children(resources, "object")
        if element.attrib.get("id")
    }
    if not object_elements:
        raise ValueError("the 3MF model does not contain any objects")

    mesh_cache: dict[str, list[trimesh.Trimesh]] = {}

    def resolve_object(object_id: str, resolving: frozenset[str] = frozenset()) -> list[trimesh.Trimesh]:
        if object_id in mesh_cache:
            return [mesh.copy() for mesh in mesh_cache[object_id]]
        if object_id in resolving:
            raise ValueError("the 3MF contains a circular component reference")

        element = object_elements.get(object_id)
        if element is None:
            raise ValueError(f"the 3MF references a missing object: {object_id}")

        resolved: list[trimesh.Trimesh] = []
        direct_mesh = _mesh_from_object(element, scale_to_mm)
        if direct_mesh is not None:
            resolved.append(direct_mesh)

        components = next(iter(_children(element, "components")), None)
        if components is not None:
            for component in _children(components, "component"):
                component_id = component.attrib.get("objectid")
                if not component_id:
                    raise ValueError("the 3MF component is missing an object reference")
                transform = _parse_transform(component.attrib.get("transform"), scale_to_mm)
                for mesh in resolve_object(component_id, resolving | {object_id}):
                    mesh.apply_transform(transform)
                    resolved.append(mesh)

        if not resolved:
            raise ValueError(f"the 3MF object {object_id} does not contain printable geometry")
        mesh_cache[object_id] = [mesh.copy() for mesh in resolved]
        return resolved

    build = next(iter(_children(root, "build")), None)
    build_items = _children(build, "item") if build is not None else []
    meshes: list[trimesh.Trimesh] = []
    if build_items:
        for item in build_items:
            object_id = item.attrib.get("objectid")
            if not object_id:
                raise ValueError("the 3MF build item is missing an object reference")
            transform = _parse_transform(item.attrib.get("transform"), scale_to_mm)
            for mesh in resolve_object(object_id):
                mesh.apply_transform(transform)
                meshes.append(mesh)
    else:
        for object_id in object_elements:
            meshes.extend(resolve_object(object_id))

    if not meshes:
        raise ValueError("the 3MF does not contain printable geometry")

    return ThreeMFModel(
        mesh=trimesh.util.concatenate(meshes),
        source_unit=source_unit,
        object_count=len(object_elements),
        build_item_count=len(build_items),
    )
