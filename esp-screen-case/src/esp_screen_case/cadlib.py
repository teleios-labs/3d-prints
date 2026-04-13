"""Reusable parametric primitives for the esp-screen-case project.

These are build123d `BasePartObject` subclasses — they drop into any
`BuildPart` context (or `Locations`, or algebra-mode composition) like
native primitives such as `Box` or `Cylinder`. Each one wraps a
construction pattern that would otherwise repeat inline.

Design notes:
    - Each subclass builds its geometry inside an isolated inner
      `BuildPart()` context. This is important: without the inner
      context, any enclosing `Locations` would bleed through and apply
      to the subclass's internal construction primitives, causing a
      double translation when `super().__init__` re-applies the same
      placement. The inner context has its own identity location stack,
      so internal geometry stays at origin until the outer builder
      places the finished primitive.
    - Internal 2D profiles are built context-free via
      `Wire.make_polygon` + `Face(...)` so there is no confusion about
      which builder they belong to.
    - Sign-convention gotchas (Plane.XZ.offset, YZ extrude direction)
      are encapsulated here and never leak to callers.
"""

from __future__ import annotations

from build123d import (
    BasePartObject,
    Box,
    BuildPart,
    Face,
    Locations,
    Mode,
    Pos,
    RotationLike,
    Wire,
    extrude,
)


def _trapezoid_yz_face(base_width: float, top_width: float, height: float) -> Face:
    """Build a trapezoidal face on the YZ plane (X=0), context-free.

    Centered in Y. Narrow base at Z=0 spans ±base_width/2. Wider top at
    Z=height spans ±top_width/2.
    """
    wire = Wire.make_polygon(
        [
            (0, -base_width / 2, 0),
            (0, base_width / 2, 0),
            (0, top_width / 2, height),
            (0, -top_width / 2, height),
        ],
        close=True,
    )
    return Face(wire)


def _xz_triangle_face(
    x0: float, x1: float, z0: float, z1: float
) -> Face:
    """Build a right-triangle face on the XZ plane (Y=0), context-free.

    Base along Z=z0 from X=x0 to X=x1, rising to a peak at (x1, z1).
    This encapsulates the `Plane.XZ` sign-convention gotcha — callers
    place the triangle using `Pos(...)` instead of offset math.
    """
    wire = Wire.make_polygon(
        [
            (x0, 0, z0),
            (x1, 0, z0),
            (x1, 0, z1),
        ],
        close=True,
    )
    return Face(wire)


class Dovetail(BasePartObject):
    """Trapezoidal dovetail prism extruded along X.

    One helper for both rails and channel cuts — the underlying shape is
    identical; the caller picks `mode=Mode.ADD` for a solid rail or
    `mode=Mode.SUBTRACT` for a matching channel cut.

    Origin:
        Centered in X (length spans ±length/2). Centered in Y (base
        spans ±base_width/2, top spans ±top_width/2). Z=0 at the narrow
        base, Z=height at the wider top.

    Prefer the thin aliases `DovetailRail` (ADD default) and
    `DovetailChannel` (SUBTRACT default) at call sites for readability.

    Args:
        length: Prism length along X.
        base_width: Narrow bottom width of the trapezoid (along Y).
        top_width: Wider top width of the trapezoid (along Y).
        height: Dovetail height along Z.
    """

    def __init__(
        self,
        length: float,
        base_width: float,
        top_width: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align=None,
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as ctx:
            face = _trapezoid_yz_face(base_width, top_width, height)
            extrude(face, amount=length / 2, both=True)
        super().__init__(part=ctx.part, rotation=rotation, align=align, mode=mode)


class DovetailRail(Dovetail):
    """Solid dovetail rail — narrow base, wider top (undercut).

    Thin ADD-mode alias over `Dovetail` for readable call sites. See
    `Dovetail` for the origin convention and argument meaning.
    """


class DovetailChannel(Dovetail):
    """Dovetail channel cut — narrow at floor, wider at ceiling.

    Thin SUBTRACT-mode alias over `Dovetail` for readable call sites.
    Defaults to SUBTRACT so it naturally carves out matching channels
    when placed inside a `BuildPart` context.
    """

    def __init__(
        self,
        length: float,
        base_width: float,
        top_width: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align=None,
        mode: Mode = Mode.SUBTRACT,
    ):
        super().__init__(
            length=length,
            base_width=base_width,
            top_width=top_width,
            height=height,
            rotation=rotation,
            align=align,
            mode=mode,
        )


class SnapBump(BasePartObject):
    """Snap bump with entry ramp — sits on top of a rail.

    Shape (side view, looking along +Y):

            ┌──────┐  <- catch top (Z = protrusion)
        ╱╱╱╱│catch │
      ╱ramp │      │
    ━━━━━━━━━━━━━━━━━━  <- rail top (Z = 0)
    ←ramp→ ←catch→

    Origin:
        Center of the catch's bottom face. Catch extends
        ±catch_length/2 along X, ±width/2 along Y, and 0 to +protrusion
        along Z. Ramp extends in -X from the catch's -X edge, rising
        from Z=0 at its far end to Z=protrusion where it meets the
        catch.

    Place with `Pos(snap_x, rail_y, rail_top_z)` so the bump sits flush
    on top of the rail at the desired X position.

    Args:
        catch_length: Flat plateau length along X (engages the pocket).
        ramp_length: Entry ramp length along X.
        width: Bump width along Y.
        protrusion: Total height above the rail top.
    """

    def __init__(
        self,
        catch_length: float,
        ramp_length: float,
        width: float,
        protrusion: float,
        rotation: RotationLike = (0, 0, 0),
        align=None,
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as ctx:
            # Catch: box with its bottom face at Z=0 (centered X/Y)
            with Locations(Pos(0, 0, protrusion / 2)):
                Box(catch_length, width, protrusion)
            # Entry ramp: right triangle on XZ plane, extruded across Y
            ramp_x_end = -catch_length / 2
            ramp_x_start = ramp_x_end - ramp_length
            ramp_face = _xz_triangle_face(
                ramp_x_start, ramp_x_end, 0, protrusion
            )
            extrude(ramp_face, amount=width / 2, both=True)

        super().__init__(part=ctx.part, rotation=rotation, align=align, mode=mode)


class SnapPocket(BasePartObject):
    """Dual-ramped snap pocket cut — deeper recess for a snap bump to click into.

    A pocket that is `extra_depth` deeper than the surrounding groove,
    with ramps on both -X and +X sides so the bump can slide in and out
    smoothly. The ramps blend from groove depth to pocket depth over
    `ramp_length` on each side.

    Shape (side view along +Y, cutting into the ceiling of a groove):

        ━━groove━━╲              ╱━━groove━━    <- groove level (Z=0)
                   ╲            ╱
                    ╲__________╱                <- pocket level (Z=+extra_depth)
                     ←  catch →
                  ←     total    →

    Origin:
        Centered on the catch in X, centered in Y (±width/2). Z=0 is
        the groove ceiling level (the level from which the pocket
        descends). Place with `Pos(snap_x, channel_y, groove_top_z)`
        to carve the pocket into an existing groove.

    Default mode is SUBTRACT so it naturally cuts into the enclosing
    body when used in a `BuildPart` context.

    Args:
        catch_length: Flat catch length along X (matches SnapBump).
        ramp_length: Length of each transition ramp on -X and +X sides.
        width: Pocket width along Y.
        extra_depth: How much deeper the pocket is than the surrounding
            groove along +Z.
    """

    # Small overshoots for OCCT boolean robustness at coincident faces.
    _FLOOR_OVERSHOOT = 0.05
    _RECESS_OVERSHOOT = 0.05
    _RAMP_EXTRA = 0.05

    def __init__(
        self,
        catch_length: float,
        ramp_length: float,
        width: float,
        extra_depth: float,
        rotation: RotationLike = (0, 0, 0),
        align=None,
        mode: Mode = Mode.SUBTRACT,
    ):
        half_catch = catch_length / 2

        floor_z = -self._FLOOR_OVERSHOOT
        recess_top_z = extra_depth + self._RECESS_OVERSHOOT
        ramp_peak_z = recess_top_z + self._RAMP_EXTRA

        with BuildPart() as ctx:
            # Main flat recess — spans only the catch region at full depth.
            # The ramp wedges below extend the cut into the ramp X regions
            # with linearly varying depth. (Earlier versions sized this box
            # to catch + 2*ramp at full depth, which made the ramp wedges
            # a strict subset of the box and contributed nothing — the
            # resulting pocket was a flat-bottomed box, not a ramped
            # detent.)
            recess_center = (floor_z + recess_top_z) / 2
            recess_height = recess_top_z - floor_z
            with Locations(Pos(0, 0, recess_center)):
                Box(catch_length, width, recess_height)

            # Entry ramp on -X side: blend from groove level at the outer
            # edge up to pocket peak where it meets the catch.
            entry_face = _xz_triangle_face(
                -half_catch - ramp_length, -half_catch, floor_z, ramp_peak_z
            )
            extrude(entry_face, amount=width / 2, both=True)

            # Exit ramp on +X side: mirror of entry. _xz_triangle_face
            # always rises at its +X endpoint, so we swap the X endpoints
            # to get the peak on the -X side of the exit region.
            exit_face = _xz_triangle_face(
                half_catch + ramp_length, half_catch, floor_z, ramp_peak_z
            )
            extrude(exit_face, amount=width / 2, both=True)

        super().__init__(part=ctx.part, rotation=rotation, align=align, mode=mode)
