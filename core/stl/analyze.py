from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple
import numpy as np
import trimesh


@dataclass
class STLFeatures:
    bbox_mm: Tuple[float, float, float]  # (x, y, z)
    footprint_bbox_mm2: float            # bbox x*y
    contact_area_mm2: float              # estimated real bed contact area
    contact_ratio: float                 # contact_area / footprint_bbox
    height_mm: float                     # z extent
    aspect_ratio: float                  # height / max(x,y)
    volume_mm3: float
    surface_area_mm2: float
    watertight: bool
    is_volume: bool

    # NEW:
    overhang_percent: float              # % faces that look “support-worthy”
    max_overhang_deg: float              # worst-case overhang angle
    likely_supports: bool                # quick boolean: do we likely need supports?
    open_edges: int                      # how many boundary edges (rough “broken-ness”)
    likely_open_top: bool                # looks like an intentionally open container
    bounds_mm: Tuple[Tuple[float, float, float], Tuple[float, float, float]]  # (min), (max)


def _estimate_contact_area_xy(mesh: trimesh.Trimesh, tol_mm: float = 0.3) -> float:
    if mesh.faces is None or len(mesh.faces) == 0:
        return 0.0

    verts = mesh.vertices
    faces = mesh.faces
    z = verts[:, 2]
    z_min = float(z.min())

    face_verts = verts[faces]  # (F, 3, 3)
    z_face = face_verts[:, :, 2]
    mask = (z_face <= (z_min + tol_mm)).all(axis=1)

    bottom_faces = face_verts[mask]
    if bottom_faces.shape[0] == 0:
        return 0.0

    a = bottom_faces[:, 0, :2]
    b = bottom_faces[:, 1, :2]
    c = bottom_faces[:, 2, :2]

    ab = b - a
    ac = c - a
    cross = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    area = 0.5 * np.abs(cross).sum()
    return float(area)


def _overhang_metrics(mesh: trimesh.Trimesh, threshold_deg: float = 55.0) -> tuple[float, float, bool]:
    """
    Compute overhang based on face normals.
    We treat faces whose normals point “down” a lot as support-worthy.
    """
    if mesh.face_normals is None or len(mesh.face_normals) == 0:
        return 0.0, 0.0, False

    n = mesh.face_normals  # (F,3)
    nz = n[:, 2]

    # Down-facing if nz < 0. For those, compute how “horizontal” they are:
    # angle_from_down = arccos(|nz|) where |nz| close to 0 => near horizontal => bad overhang
    down = nz < -1e-6
    if not np.any(down):
        return 0.0, 0.0, False

    nz_abs = np.clip(np.abs(nz[down]), 0.0, 1.0)
    ang = np.degrees(np.arccos(nz_abs))  # 0=vertical, 90=horizontal
    max_overhang = float(np.max(ang)) if ang.size else 0.0

    # support-worthy if close to horizontal (large angle)
    support_worthy = ang >= threshold_deg
    pct = float(100.0 * np.mean(support_worthy)) if ang.size else 0.0

    likely = pct >= 2.0 or max_overhang >= (threshold_deg + 10)  # simple heuristic
    return pct, max_overhang, bool(likely)


def _boundary_edge_count(mesh: trimesh.Trimesh) -> int:
    """
    Boundary edges exist when mesh is not watertight.
    This roughly correlates to “broken-ness” (holes, open seams).
    """
    try:
        be = mesh.edges_boundary
        return int(len(be)) if be is not None else 0
    except Exception:
        return 0


def _likely_open_top(mesh: trimesh.Trimesh, tol_mm: float = 0.4) -> bool:
    """
    Heuristic: Many open edges near top plane + mostly flat top rim suggests
    an intentionally open container, not random holes.
    """
    if mesh.is_watertight:
        return False

    z = mesh.vertices[:, 2]
    z_max = float(z.max())

    # boundary edges near top
    try:
        be = mesh.edges_boundary
        if be is None or len(be) == 0:
            return False
        v = mesh.vertices
        e = be  # (E,2)
        ez = (v[e[:, 0], 2] + v[e[:, 1], 2]) / 2.0
        near_top = ez >= (z_max - tol_mm)
        ratio = float(np.mean(near_top)) if len(ez) else 0.0
        # If most boundary edges live near the top plane, it’s likely an open-top shape
        return ratio >= 0.70
    except Exception:
        return False


def analyze_stl(path: str) -> Dict[str, Any]:
    mesh = trimesh.load(path, force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate([g for g in mesh.geometry.values()])

    x, y, z = [float(v) for v in mesh.extents]
    footprint_bbox = float(x * y)

    height = float(z)
    denom = max(x, y) if max(x, y) > 0 else 1.0
    aspect = float(height / denom)

    bmin = tuple(float(v) for v in mesh.bounds[0])
    bmax = tuple(float(v) for v in mesh.bounds[1])

    contact_area = _estimate_contact_area_xy(mesh, tol_mm=0.3)
    contact_ratio = float(contact_area / footprint_bbox) if footprint_bbox > 0 else 0.0

    overhang_pct, max_overhang_deg, likely_supports = _overhang_metrics(mesh, threshold_deg=55.0)

    open_edges = _boundary_edge_count(mesh)
    likely_open_top = _likely_open_top(mesh, tol_mm=0.5)

    feats = STLFeatures(
        bbox_mm=(x, y, z),
        footprint_bbox_mm2=footprint_bbox,
        contact_area_mm2=contact_area,
        contact_ratio=contact_ratio,
        height_mm=height,
        aspect_ratio=aspect,
        volume_mm3=float(mesh.volume) if mesh.is_volume else 0.0,
        surface_area_mm2=float(mesh.area),
        watertight=bool(mesh.is_watertight),
        is_volume=bool(mesh.is_volume),
        overhang_percent=float(round(overhang_pct, 2)),
        max_overhang_deg=float(round(max_overhang_deg, 1)),
        likely_supports=bool(likely_supports),
        open_edges=int(open_edges),
        likely_open_top=bool(likely_open_top),
        bounds_mm=(bmin, bmax),
    )
    return asdict(feats)