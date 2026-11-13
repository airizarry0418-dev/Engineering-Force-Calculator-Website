"""
CISC 106 Final Project: 2D Force Vector Calculator
Author: Alex Irizarry
Description: A Drafter web application that helps engineering students break down
             2D force vectors into x/y components and calculate overall magnitude
             and direction angle.
"""

import sys
import types
from dataclasses import dataclass
import math

# =============================================================================
# ENVIRONMENT COMPATIBILITY FIX FOR PYTHON 3
# =============================================================================
if "crypto_tools" not in sys.modules:
    mock_crypto = types.ModuleType("crypto_tools")
    mock_crypto.decrypt_text = lambda text, key=None: text
    mock_crypto.encrypt_text = lambda text, key=None: text
    mock_crypto.hash_text = lambda text: text
    sys.modules["crypto_tools"] = mock_crypto

from drafter import (
    route, Page, Text, Button, TextBox, Row,
    start_server, set_site_information
)
from bakery import assert_equal


# =============================================================================
# DATACLASS DEFINITIONS
# =============================================================================

@dataclass
class Force:
    """Represents an individual 2D force vector with components."""
    name: str
    magnitude: float
    angle: float
    fx: float
    fy: float


@dataclass
class State:
    """Holds the complete application state across routes."""
    forces: list[Force]
    resultant_magnitude: float
    resultant_angle: float
    status_message: str


# =============================================================================
# HELPER / MATH FUNCTIONS
# =============================================================================

def calculate_fx(magnitude: float, angle_degrees: float) -> float:
    """Calculates the horizontal component (Fx) of a vector given degrees."""
    radians = math.radians(angle_degrees)
    return round(magnitude * math.cos(radians), 2)


def calculate_fy(magnitude: float, angle_degrees: float) -> float:
    """Calculates the vertical component (Fy) of a vector given degrees."""
    radians = math.radians(angle_degrees)
    return round(magnitude * math.sin(radians), 2)


def compute_resultant(forces: list[Force]) -> tuple[float, float]:
    """
    Computes total magnitude and direction angle (degrees) from a list of Force items.
    Iterates over attributes of Force instances in the list.
    """
    if not forces:
        return 0.0, 0.0

    total_fx = 0.0
    total_fy = 0.0

    for f in forces:
        total_fx += f.fx
        total_fy += f.fy

    net_magnitude = round(math.sqrt(total_fx**2 + total_fy**2), 2)
    radians = math.atan2(total_fy, total_fx)
    net_angle = round(math.degrees(radians), 2)

    return net_magnitude, net_angle


def create_initial_state() -> State:
    """Creates a default state with no active forces."""
    return State(
        forces=[],
        resultant_magnitude=0.0,
        resultant_angle=0.0,
        status_message="Welcome! Add a force or load a preset to get started."
    )


# =============================================================================
# DRAFTER ROUTES & PAGES
# =============================================================================

@route
def index(state: State) -> Page:
    """Route 1 / Page 1: Renders the main dashboard with active forces and net results."""
    force_rows = []
    for f in state.forces:
        force_rows.append(
            Text(f"• {f.name}: {f.magnitude} N @ {f.angle}° | Fx: {f.fx} N, Fy: {f.fy} N")
        )

    if not force_rows:
        force_rows.append(Text("No forces currently added."))

    header = [
        Text("2D Force Vector Calculator", bold=True),
        Text(f"Status: {state.status_message}"),
        Text("Current Applied Forces:")
    ]

    footer = [
        Text("---"),
        Text(f"Net Resultant Magnitude: {state.resultant_magnitude} N"),
        Text(f"Net Resultant Angle: {state.resultant_angle}°"),
        Text("---"),
        Row([
            Button("Add New Force", show_add_force_page),
            Button("View Component Breakdown", show_summary_page),
            Button("Load Engineering Presets", load_preset_vectors),
            Button("Clear All Forces", clear_forces),
            Button("Formula Reference", show_help_page)
        ])
    ]

    return Page(state, header + force_rows + footer)


@route
def show_add_force_page(state: State) -> Page:
    """Route 2 / Page 2: Renders the input form page to accept a new force vector."""
    return Page(
        state,
        [
            Text("Add a New Force Vector", bold=True),
            Text("Enter force details below:"),
            TextBox("force_name", "e.g., Cable Tension A"),
            TextBox("magnitude", "Magnitude (N)"),
            TextBox("angle", "Angle (Degrees relative to +x axis)"),
            Row([
                Button("Submit Force", add_force),
                Button("Cancel", index)
            ])
        ]
    )


@route
def add_force(state: State, force_name: str, magnitude: str, angle: str) -> Page:
    """Route 3: Validates user input, constructs a Force, updates State, and returns Home."""
    if not force_name.strip():
        state.status_message = "Error: Force name cannot be empty."
        return index(state)

    try:
        mag_val = float(magnitude)
        ang_val = float(angle)
    except ValueError:
        state.status_message = "Error: Magnitude and Angle must be valid numbers."
        return index(state)

    if mag_val < 0:
        state.status_message = "Error: Force magnitude cannot be negative."
        return index(state)

    fx = calculate_fx(mag_val, ang_val)
    fy = calculate_fy(mag_val, ang_val)
    new_force = Force(force_name.strip(), mag_val, ang_val, fx, fy)

    state.forces.append(new_force)
    state.resultant_magnitude, state.resultant_angle = compute_resultant(state.forces)
    state.status_message = f"Successfully added '{new_force.name}'!"

    return index(state)


@route
def show_summary_page(state: State) -> Page:
    """Route 4 / Page 3: Displays itemized breakdown of horizontal and vertical force components."""
    summary_lines = [Text("Component Summary Breakdown", bold=True)]
    total_x = 0.0
    total_y = 0.0

    for f in state.forces:
        summary_lines.append(Text(f"{f.name} -> Fx = {f.fx} N, Fy = {f.fy} N"))
        total_x += f.fx
        total_y += f.fy

    summary_lines.extend([
        Text("---"),
        Text(f"Sum of Horizontal Forces (ΣFx): {round(total_x, 2)} N"),
        Text(f"Sum of Vertical Forces (ΣFy): {round(total_y, 2)} N"),
        Button("Back to Home", index)
    ])

    return Page(state, summary_lines)


@route
def load_preset_vectors(state: State) -> Page:
    """Route 5 / Page 4: Populates state with standard engineering statics example forces."""
    f1 = Force("Weight (Gravity)", 100.0, 270.0, calculate_fx(100.0, 270.0), calculate_fy(100.0, 270.0))
    f2 = Force("Cable Tension 1", 150.0, 45.0, calculate_fx(150.0, 45.0), calculate_fy(150.0, 45.0))

    state.forces = [f1, f2]
    state.resultant_magnitude, state.resultant_angle = compute_resultant(state.forces)
    state.status_message = "Loaded standard engineering 2-force equilibrium preset."

    return index(state)


@route
def clear_forces(state: State) -> Page:
    """Route 6: Resets all forces and resultant calculations in the state."""
    if not state.forces:
        state.status_message = "State is already clean."
        return index(state)

    state.forces = []
    state.resultant_magnitude = 0.0
    state.resultant_angle = 0.0
    state.status_message = "All forces cleared successfully."

    return index(state)


@route
def show_help_page(state: State) -> Page:
    """Route 7 / Page 5: Provides vector statics background and formula explanations."""
    return Page(
        state,
        [
            Text("Vector Math Formulas & Reference", bold=True),
            Text("1. Horizontal Component: Fx = F * cos(θ)"),
            Text("2. Vertical Component: Fy = F * sin(θ)"),
            Text("3. Resultant Magnitude: FR = sqrt((ΣFx)^2 + (ΣFy)^2)"),
            Text("4. Direction Angle: θ = arctan(ΣFy / ΣFx)"),
            Button("Back to Home", index)
        ]
    )


# =============================================================================
# UNIT TESTS
# =============================================================================

def test_calculate_fx():
    """Unit tests for calculate_fx helper."""
    assert_equal(calculate_fx(100.0, 0.0), 100.0)
    assert_equal(calculate_fx(100.0, 90.0), 0.0)
    assert_equal(calculate_fx(100.0, 180.0), -100.0)


def test_calculate_fy():
    """Unit tests for calculate_fy helper."""
    assert_equal(calculate_fy(100.0, 0.0), 0.0)
    assert_equal(calculate_fy(100.0, 90.0), 100.0)
    assert_equal(calculate_fy(100.0, 270.0), -100.0)


def test_compute_resultant():
    """Unit tests for resultant calculations."""
    f1 = Force("F1", 3.0, 0.0, 3.0, 0.0)
    f2 = Force("F2", 4.0, 90.0, 0.0, 4.0)
    mag, ang = compute_resultant([f1, f2])
    assert_equal(mag, 5.0)
    assert_equal(ang, 53.13)

    empty_mag, empty_ang = compute_resultant([])
    assert_equal(empty_mag, 0.0)
    assert_equal(empty_ang, 0.0)


def test_routes():
    """Unit tests verifying route state changes and page rendering."""
    st = create_initial_state()
    assert_equal(isinstance(index(st), Page), True)
    assert_equal(isinstance(show_add_force_page(st), Page), True)
    assert_equal(isinstance(show_help_page(st), Page), True)

    add_force(st, "Pull", "10", "0")
    assert_equal(len(st.forces), 1)
    assert_equal(st.resultant_magnitude, 10.0)
    assert_equal(st.resultant_angle, 0.0)
    assert_equal(isinstance(show_summary_page(st), Page), True)

    clear_forces(st)
    assert_equal(len(st.forces), 0)
    assert_equal(st.resultant_magnitude, 0.0)

    load_preset_vectors(st)
    assert_equal(len(st.forces), 2)


test_calculate_fx()
test_calculate_fy()
test_compute_resultant()
test_routes()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Note: Keep set_site_information commented out if it triggers
     UpdatedConfiguration sync errors in Drafter 2.2.0 local browser mode.
     set_site_information(
         author="Alex Irizarry",
         description="Statics vector component solver web application built with Drafter.",
         sources=["Python math module", "Drafter documentation"],
         planning=["Design Document"],
         links=["https://udel.edu"]
     )
    start_server(create_initial_state())
