"""Shared dimensions and constants for CrowPanel 7" case design.

All measurements in millimeters. Source: Elecrow STEP file + datasheet.
Board: CrowPanel Advance 7" (DIS02170A V1.3/V1.4)
"""

# --- Board dimensions (from STEP model) ---
BOARD_LENGTH = 181.26  # X axis
BOARD_HEIGHT = 108.36  # Y axis
BOARD_DEPTH = 16.00    # Z axis (total thickness)

# --- Display ---
DISPLAY_ACTIVE_WIDTH = 156.0
DISPLAY_ACTIVE_HEIGHT = 87.0

# --- USB-C port (right edge, centered vertically) ---
USB_EDGE = "right"  # X ≈ 170mm
USB_CENTER_Y = 52.0  # approximate center from board bottom
USB_WIDTH = 8.9
USB_HEIGHT = 4.2

# --- Rail/channel system ---
RAIL_WIDTH = 10.0
RAIL_DEPTH = 7.0
RAIL_CLEARANCE = 0.1       # total clearance (0.05 each side) — 0.5 and 0.3 both too loose
CHANNEL_WIDTH = RAIL_WIDTH + RAIL_CLEARANCE  # 10.5mm
CHANNEL_DEPTH = RAIL_DEPTH + 0.3             # 7.3mm vertical clearance

# --- Bracket ---
BRACKET_WALL = 3.0          # wall thickness around structural features
BRACKET_ARM_LENGTH = 60.0   # how far arms extend from hub
BRACKET_HUB_WIDTH = 50.0    # central hub X dimension
BRACKET_HUB_HEIGHT = 30.0   # central hub Y dimension
BRACKET_THICKNESS = 4.0     # Z thickness of bracket base

# --- Mounting ---
SCREW_HOLE_DIAMETER = 4.0   # for M3 + clearance (drywall anchors)
SCREW_HEAD_DIAMETER = 7.0   # M3 screw head clearance

# --- Snap lock ---
# Design: small bump on rail slides in a shallow groove in the channel ceiling.
# Groove runs full length, pocket at end is slightly deeper for snap click.
# Both pocket edges ramp to allow smooth engagement + moderate release force.
SNAP_PROTRUSION = 1.0       # bump height (small — fits in channel clearance groove)
SNAP_RAMP_LENGTH = 3.0      # 3mm ramp at ~18° angle for 1.0mm rise
SNAP_CATCH_LENGTH = 1.5     # flat catch surface length
SNAP_POCKET_EXTRA = 0.4     # pocket is this much deeper than groove (snap drop)
SNAP_POCKET_RAMP = 2.0      # 2mm ramps inside pocket on both sides

# --- Printer tolerances ---
PRINTER_UNDERSIZING = 0.19  # Centauri Carbon 2 average (parts print smaller)
