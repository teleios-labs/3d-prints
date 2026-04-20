"""Shared dimensions and constants for CrowPanel 7" case design.

All measurements in millimeters. Source: Elecrow STEP file + datasheet
and user-measured values.
Board: CrowPanel Advance 7" (DIS02170A V1.3/V1.4)
"""

# --- Board dimensions (from STEP model) ---
BOARD_LENGTH = 177.61  # X axis — user-measured 2026-04-19 (prior 158.67 was mis-measured)
BOARD_HEIGHT = 104.16  # Y axis — user-measured 2026-04-14
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
USB_CENTER_Y_FROM_BOTTOM = 51.22  # from the bottom of the board — user-measured 2026-04-14
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

# Interior floor is two-tier: thin (Z=3) everywhere except a narrow strip
# down the middle that keeps the full back-plate thickness above the
# dovetail channel (Z=14.3). The thick strip is slightly wider than the
# channel for wall integrity.
CASE_BACK_PLATE_THIN = 3.0         # thin back plate thickness (mm)
CASE_THICK_STRIP_HALF_WIDTH = 6.6  # X half-width of the thick strip (channel top width / 2 + 1 mm margin)

# Interior standoffs — rise from the THIN interior floor to the PCB back.
CASE_STANDOFF_OD = 6.0
CASE_STANDOFF_PILOT_DIAMETER = 2.5   # self-tapping M3 into plastic
CASE_STANDOFF_HEIGHT = 19.0          # thin floor (3) + 19 = standoff top (22), PCB back lands at 22

# Bracket recess (pocket in the case back that accepts the hub flush).
# The recess only covers the portion of the hub that's INSIDE the case
# when seated: the upper hub (rail + lead-in strip). The shelf flange is
# below the case, supporting the case bottom on its overhangs.
CASE_BRACKET_RECESS_X = BRACKET_HUB_X
CASE_BRACKET_RECESS_Y = BRACKET_RAIL_LENGTH + BRACKET_RAIL_LEAD_IN
CASE_BRACKET_RECESS_DEPTH = BRACKET_HUB_Z

# --- Printer tolerances ---
PRINTER_UNDERSIZING = 0.19  # Centauri Carbon 2 average (parts print smaller)
