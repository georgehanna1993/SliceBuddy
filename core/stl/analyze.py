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

    # Overhang/support heuristics
    overhang_percent: float
    max_overhang_deg: float
    likely_supports: bool

    # Mesh integrity diagnostics
    boundary_edges: int
    nonmanifold_edges: int
    open_edges: int                      # boundary + nonmanifold (simple)
    degenerate_faces: int                # NEW: zero/near-zero area triangles
    likely_open_top: bool
    mesh_issue: str

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
    if mesh.face_normals is None or len(mesh.face_normals) == 0:
        return 0.0, 0.0, False

    n = mesh.face_normals
    nz = n[:, 2]

    down = nz < -1e-6
    if not np.any(down):
        return 0.0, 0.0, False

    nz_abs = np.clip(np.abs(nz[down]), 0.0, 1.0)
    ang = np.degrees(np.arccos(nz_abs))  # 0=vertical, 90=horizontal
    max_overhang = float(np.max(ang)) if ang.size else 0.0

    support_worthy = ang >= threshold_deg
    pct = float(100.0 * np.mean(support_worthy)) if ang.size else 0.0

    likely = pct >= 2.0 or max_overhang >= (threshold_deg + 10)
    return float(pct), float(max_overhang), bool(likely)


def _edge_histogram_counts(mesh: trimesh.Trimesh) -> tuple[int, int]:
    """Return (boundary_edges, nonmanifold_edges) computed from face edge usage counts."""
    if mesh.faces is None or len(mesh.faces) == 0:
        return 0, 0

    f = np.asarray(mesh.faces, dtype=np.int64)

    # Build all edges from faces: (0,1), (1,2), (2,0)
    e01 = f[:, [0, 1]]
    e12 = f[:, [1, 2]]
    e20 = f[:, [2, 0]]
    edges = np.vstack([e01, e12, e20])

    # Normalize direction: sort each edge so (a,b) == (b,a)
    edges = np.sort(edges, axis=1)

    # Count occurrences using tuples (safe across numpy versions / contiguity)
    counts: Dict[tuple[int, int], int] = {}
    for a, b in edges:
        key = (int(a), int(b))
        counts[key] = counts.get(key, 0) + 1

    boundary = sum(1 for c in counts.values() if c == 1)
    nonmanifold = sum(1 for c in counts.values() if c >= 3)
    return int(boundary), int(nonmanifold)


def _degenerate_face_count(mesh: trimesh.Trimesh, eps: float = 1e-10) -> int:
    """Count triangles with near-zero area."""
    try:
        tris = mesh.triangles  # (F,3,3)
        a = tris[:, 0, :]
        b = tris[:, 1, :]
        c = tris[:, 2, :]
        ab = b - a
        ac = c - a
        cross = np.cross(ab, ac)
        area2 = np.linalg.norm(cross, axis=1)  # 2*area
        return int(np.sum(area2 <= eps))
    except Exception:
        return 0


def _likely_open_top_from_boundary(mesh: trimesh.Trimesh, boundary_edges: int, tol_mm: float = 0.5) -> bool:
    if boundary_edges <= 0:
        return False

    try:
        f = mesh.faces.astype(np.int64)
        e01 = f[:, [0, 1]]
        e12 = f[:, [1, 2]]
        e20 = f[:, [2, 0]]
        edges = np.vstack([e01, e12, e20])
        edges = np.sort(edges, axis=1)

        edges_view = edges.view([("a", edges.dtype), ("b", edges.dtype)])
        uniq, counts = np.unique(edges_view, return_counts=True)

        boundary_mask = (counts == 1)
        boundary_edges_arr = uniq[boundary_mask].view(edges.dtype).reshape(-1, 2)
        if boundary_edges_arr.size == 0:
            return False

        v = mesh.vertices
        z_max = float(v[:, 2].max())
        ez = (v[boundary_edges_arr[:, 0], 2] + v[boundary_edges_arr[:, 1], 2]) / 2.0
        near_top = ez >= (z_max - tol_mm)
        ratio = float(np.mean(near_top)) if ez.size else 0.0
        return ratio >= 0.70
    except Exception:
        return False


def _mesh_issue_summary(watertight: bool, is_volume: bool, boundary_edges: int, nonmanifold_edges: int, degenerate_faces: int) -> str:
    if watertight and is_volume:
        return "ok"

    parts = []
    if boundary_edges > 0:
        parts.append(f"holes/open rims (boundary edges): {boundary_edges}")
    if nonmanifold_edges > 0:
        parts.append(f"non-manifold edges: {nonmanifold_edges}")
    if degenerate_faces > 0:
        parts.append(f"degenerate triangles: {degenerate_faces}")
    if not is_volume:
        parts.append("not a valid closed volume (volume may be unreliable)")

    if not parts:
        parts.append("mesh may be invalid (possible self-intersections/overlaps)")

    return "; ".join(parts)


def analyze_stl(path: str) -> Dict[str, Any]:
    mesh = trimesh.load(path, force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate([g for g in mesh.geometry.values()])

    # (Optional) Keep your debug for now; remove later
    print("DEBUG CHECKS ----------------")
    print("is_watertight:", mesh.is_watertight)
    print("is_volume:", mesh.is_volume)
    print("is_winding_consistent:", getattr(mesh, "is_winding_consistent", None))
    print("is_self_intersecting:", getattr(mesh, "is_self_intersecting", None))
    print("euler_number:", getattr(mesh, "euler_number", None))
    print("--------------------------------")

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

    boundary_edges, nonmanifold_edges = _edge_histogram_counts(mesh)
    degenerate_faces = _degenerate_face_count(mesh)

    likely_open_top = _likely_open_top_from_boundary(mesh, boundary_edges=boundary_edges, tol_mm=0.5)

    watertight = bool(mesh.is_watertight)
    is_volume = bool(mesh.is_volume)

    mesh_issue = _mesh_issue_summary(
        watertight=watertight,
        is_volume=is_volume,
        boundary_edges=boundary_edges,
        nonmanifold_edges=nonmanifold_edges,
        degenerate_faces=degenerate_faces,
    )

    feats = STLFeatures(
        bbox_mm=(x, y, z),
        footprint_bbox_mm2=footprint_bbox,
        contact_area_mm2=contact_area,
        contact_ratio=contact_ratio,
        height_mm=height,
        aspect_ratio=aspect,
        volume_mm3=float(mesh.volume) if mesh.is_volume else 0.0,
        surface_area_mm2=float(mesh.area),
        watertight=watertight,
        is_volume=is_volume,
        overhang_percent=float(round(overhang_pct, 2)),
        max_overhang_deg=float(round(max_overhang_deg, 1)),
        likely_supports=bool(likely_supports),
        boundary_edges=int(boundary_edges),
        nonmanifold_edges=int(nonmanifold_edges),
        open_edges=int(boundary_edges + nonmanifold_edges),
        degenerate_faces=int(degenerate_faces),
        likely_open_top=bool(likely_open_top),
        mesh_issue=str(mesh_issue),
        bounds_mm=(bmin, bmax),
    )
    return asdict(feats)