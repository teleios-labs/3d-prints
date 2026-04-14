"""Shared dimensions and constants for CrowPanel 7" case design.

All measurements in millimeters. Source: Elecrow STEP file + datasheet
and user-measured values.
Board: CrowPanel Advance 7" (DIS02170A V1.3/V1.4)
"""

# --- Board dimensions (from STEP model) ---
BOARD_LENGTH = 181.26  # X axis
BOARD_HEIGHT = 108.36  # Y axis
BOARD_DEPTH = 16.00    # Z axis (total thickness, back components → display glass)

# --- Display ---
DISPLAY_ACTIVE_WIDTH = 156.0
DISPLAY_ACTIVE_HEIGHT = 87.0

# --- Board-back clearance (user-measured) ---
# Tallest component on the back of the PCB is ~7mm from the PCB surface.
# Standoffs must lift the PCB clear of this by ≥1mm.
BACK_COMPONENT_HEIGHT = 7.0

# --- Board mounting holes (user-measured with calipers) ---
# 4× M3 clearance holes, one in each corner, 3.2mm from both edges to
# the hole center. Assumed symmetric on both axes.
BOARD_HOLE_EDGE_OFFSET = 3.2
BOARD_HOLE_DIAMETER = 3.2  # M3 clearance

# --- USB-C port (right edge, centered vertically) ---
USB_EDGE = "right"            # X = +BOARD_LENGTH/2
USB_CENTER_Y_FROM_BOTTOM = 52.0  # from the bottom of the board
USB_WIDTH = 8.9
USB_HEIGHT = 4.2
USB_CLEARANCE = 0.5  # each side

# --- Rail/channel system (validated by tolerance_test) ---
# Clearance history (PLA tests):
#   0.5mm total — too loose
#   0.3mm total — still slightly loose
#   0.1mm total — good PLA fit
# For PETG add 0.1mm extra for die swell → 0.2mm total.
RAIL_WIDTH = 10.0              # narrow base of the dovetail
RAIL_TOP_WIDTH = 11.0          # wider top (1mm taper per side)
RAIL_DEPTH = 7.0
RAIL_CLEARANCE = 0.2           # total, split evenly

CHANNEL_BASE_WIDTH = RAIL_WIDTH + RAIL_CLEARANCE       # 10.2
CHANNEL_TOP_WIDTH = RAIL_TOP_WIDTH + RAIL_CLEARANCE    # 11.2
CHANNEL_DEPTH = RAIL_DEPTH + 0.3                        # 7.3 vertical slop

# --- Wall bracket ---
BRACKET_HUB_X = 30.0           # width
BRACKET_HUB_Y = 73.0           # height (50mm rail + 15mm shelf + 8mm top lead-in strip)
BRACKET_HUB_Z = 4.0            # thickness (wall to hub front)
BRACKET_RAIL_LENGTH = 50.0     # dovetail rail length (along Y, vertical)
BRACKET_SHELF_Y = 15.0         # solid shelf height (bottom of hub, no rail)
BRACKET_RAIL_LEAD_IN = 8.0     # lead-in strip above the rail (hosts top anchor hole)
BRACKET_SHELF_X = 40.0         # shelf flange X width (wider than the 30mm upper hub
                                # so the case bottom lands on the 5mm 'ears' that
                                # stick out beyond the bracket recess on the case)

# --- Mounting hardware ---
SCREW_HOLE_DIAMETER = 4.0      # M3 + clearance (drywall anchors + bracket)
SCREW_HEAD_DIAMETER = 7.0      # M3 head clearance

# --- Case (monocoque back tray) ---
CASE_MOUNT_ORIENTATION = "landscape"
CASE_WALL_THICKNESS = 2.0
CASE_BOARD_CLEARANCE = 0.3     # radial clearance around the board inside the tray
CASE_BACK_PLATE_ABOVE_CHANNEL = 3.0  # material above the dovetail channel floor

# Interior standoffs
CASE_STANDOFF_OD = 6.0
CASE_STANDOFF_PILOT_DIAMETER = 2.5   # self-tapping M3 into plastic
CASE_STANDOFF_HEIGHT = BACK_COMPONENT_HEIGHT + 1.0  # 8.0 — clears back components + 1mm

# Bracket recess (pocket in the case back that accepts the hub flush)
CASE_BRACKET_RECESS_X = BRACKET_HUB_X
CASE_BRACKET_RECESS_Y = BRACKET_HUB_Y
CASE_BRACKET_RECESS_DEPTH = BRACKET_HUB_Z

# --- Printer tolerances ---
PRINTER_UNDERSIZING = 0.19  # Centauri Carbon 2 average (parts print smaller)
