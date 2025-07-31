import numpy as np
import matplotlib.pyplot as plt
import datetime
# -- Add this at the top of your script --
ANIMAL_SPECIES = "51U6-M"
N_ANIMALS = 20
ARENA_SIZE = 20.0  # Edge length in meters
CENTER = np.array([0.0, 0.0])
DT = 0.1  # Time step in seconds
TOTAL_TIME = 1200  # Total simulation time in seconds
LED_WAVELENGTHS = [
    400.0, 678.1, 523.4, 411.9, 615.5,
    488.2, 551.7, 692.3, 430.8, 501.0,
    644.6, 576.9, 700.0, 455.1, 660.4,
    539.8, 472.5, 603.2, 588.0, 405.7
]
# Corner positions
CORNERS = {
    "top_left": np.array([-10.0, 10.0]),
    "top_right": np.array([10.0, 10.0]),
    "bottom_right": np.array([10.0, -10.0]),
    "bottom_left": np.array([-10.0, -10.0]),
}

def repulsive_pulse(time, freq):
    """Check if a repulsive pulse is active at the given time."""
    period = 1 / freq
    return np.isclose(time % period, 0, atol=DT / 2)
def appetitive_pulse(time, freq):
    """Check if a attractive pulse is active at the given time."""
    period = 1 / freq
    return np.isclose(time % period, 13, atol=DT / 2)

def compute_attraction_force(position, source, radius, strength=2.0):
    """Attractive force within a given radius."""
    delta = source - position
    distance = np.linalg.norm(delta)
    if distance < radius and distance > 1e-6:
        return strength * delta / distance
    return np.zeros(2)

def compute_repulsion_force(position, source, strength=10.0, epsilon=1e-3):
    """Repulsive force, short range."""
    delta = position - source
    distance = np.linalg.norm(delta)
    if distance > epsilon:
        return strength * delta / (distance**2)
    return np.zeros(2)

def reflect_edges(position):
    """Keep the animal inside the square arena by reflecting off the walls."""
    for i in range(2):
        if position[i] < -ARENA_SIZE / 2:
            position[i] = -ARENA_SIZE / 2 + abs(position[i] + ARENA_SIZE / 2)
        elif position[i] > ARENA_SIZE / 2:
            position[i] = ARENA_SIZE / 2 - abs(position[i] - ARENA_SIZE / 2)
    return position

def sample_step_length(mu=1.31, sigma=0.45):
    """Sample a positive step length from a normal distribution."""
    step = np.random.normal(mu, sigma)
    return max(step, 0.2)

def sample_course_interval(mu=10.0, sigma=8.0):
    """Sample a positive interval for direction persistence (in seconds)."""
    interval = np.random.normal(mu, sigma)
    return max(interval, 0.5)

def plot_trajectory(positions, subject_number = -1):
    """Plot the trajectory and arena/corners."""
    plt.figure(figsize=(8, 8))
    plt.plot([-10, 10, 10, -10, -10], [10, 10, -10, -10, 10], "k--", linewidth=1)
    plt.scatter(*CORNERS["top_left"], c="red", label="Top Left: LED Pulse 20s")
    plt.scatter(*CORNERS["top_right"], c="blue", label="Top Right: LED  + LiPS")
    plt.scatter(*CORNERS["bottom_right"], c="gray", label="Bottom Right: Neutral")
    plt.scatter(*CORNERS["bottom_left"], c="green", label="Bottom Left: LiPS")
    plt.plot(positions[:, 0], positions[:, 1], "b-", alpha=0.7, label="Trajectory")
    plt.scatter(0, 0, c="orange", marker="*", s=150, label="Start")
    plt.xlim(-11, 11)
    plt.ylim(-11, 11)
    plt.xlabel("X position (m)")
    plt.ylabel("Y position (m)")
    plt.legend(loc="upper right")
    plt.grid(True)
    if subject_number > -1:
      plt.savefig(f"subject_{subject_number}_arena.png", dpi=300, bbox_inches="tight")


def clamp_angle_between_vectors(vec_from, vec_to, max_angle_deg=150):
    """
    Clamp the angle between two vectors to a maximum allowed in degrees.

    :param vec_from: Current direction vector (normalized).
    :param vec_to: Proposed direction vector (normalized).
    :param max_angle_deg: Maximum allowed angle change (degrees, symmetric).
    :return: New direction vector (normalized).
    """
    max_angle_rad = np.deg2rad(max_angle_deg)
    # Normalize both
    vec_from = vec_from / (np.linalg.norm(vec_from) + 1e-12)
    vec_to = vec_to / (np.linalg.norm(vec_to) + 1e-12)
    # Calculate angle
    dot = np.clip(np.dot(vec_from, vec_to), -1.0, 1.0)
    angle = np.arccos(dot)
    if angle <= max_angle_rad:
        return vec_to
    # Clamp: rotate vec_from by max_angle_deg in direction of vec_to
    cross = np.cross(vec_from, vec_to)
    sign = np.sign(cross) if cross != 0 else 1  # 2D: out of plane is scalar
    # Build 2D rotation matrix
    theta = max_angle_rad * sign
    rot_matrix = np.array([[np.cos(theta), -np.sin(theta)],
                           [np.sin(theta),  np.cos(theta)]])
    clamped = rot_matrix @ vec_from
    return clamped / (np.linalg.norm(clamped) + 1e-12)

def interpolate_direction(old_dir, new_dir, alpha):
    """
    Interpolate between two directions with weight alpha (0=old, 1=new).
    Returns a normalized vector.
    """
    vec = (1 - alpha) * old_dir + alpha * new_dir
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-9 else old_dir

def simulate_trajectory(total_time=TOTAL_TIME, dt=DT, seed=42):
    #np.random.seed(seed)
    n_steps = int(total_time / dt)
    position = CENTER.copy()
    positions = np.zeros((n_steps, 2))
    times = np.zeros(n_steps)
    t = 0.0
    step = 0

    direction = np.random.randn(2)
    direction = direction / np.linalg.norm(direction)
    distance_left = 0
    course_time_left = 0

    # For smooth transition
    prev_direction = direction
    next_direction = direction
    transition_steps = 0
    transition_total_steps = 1

    while step < n_steps:
        if course_time_left <= 0 or distance_left <= 0:
            # Start a new bout
            course_time_left = sample_course_interval()
            distance_left = sample_step_length()
            # Propose a new direction
            random_dir = np.random.randn(2)
            random_dir /= np.linalg.norm(random_dir)
            force = compute_total_force(position, t)
            combined = 0.7 * random_dir + 0.3 * force / (np.linalg.norm(force) + 1e-9)
            if np.linalg.norm(combined) < 1e-6:
                combined = random_dir
            proposed = combined / np.linalg.norm(combined)
            # Clamp direction change to ≤150°
            next_direction = clamp_angle_between_vectors(direction, proposed, max_angle_deg=150)
            prev_direction = direction
            # Interpolate over first 1 second (or up to bout duration)
            transition_total_steps = min(int(1.0 / dt), int(course_time_left / dt))
            transition_steps = 0
            # Speed for this bout
            movement_speed = distance_left / course_time_left
        # Smoothly interpolate direction during first 1s of a bout
        if transition_steps < transition_total_steps:
            alpha = transition_steps / transition_total_steps
            direction = interpolate_direction(prev_direction, next_direction, alpha)
            transition_steps += 1
        else:
            direction = next_direction
        # Forces still gently bend the path
        force = compute_total_force(position, t)
        if np.linalg.norm(force) > 1e-9:
            force_dir = force / (np.linalg.norm(force) + 1e-9)
            direction = 0.97 * direction + 0.03 * force_dir
            direction = direction / np.linalg.norm(direction)
        # Step movement
        step_move = direction * movement_speed * dt
        position = position + step_move
        position = reflect_edges(position)
        positions[step] = position
        times[step] = t
        t += dt
        step += 1
        distance_left -= np.linalg.norm(step_move)
        course_time_left -= dt
    return positions, times

def compute_total_force(position, t):
    """Sum all the forces on the animal at time t."""
    force = np.zeros(2)
    # Repulsive pulse: Top left every 20s (0.05 Hz)
    if repulsive_pulse(t, freq=0.05):
        force += compute_repulsion_force(position, CORNERS["top_left"])
    # Appetitive pulse: Top left every 20s (0.05 Hz)
    if appetitive_pulse(t, freq=0.05):
        force += compute_attraction_force(position, CORNERS["top_left"], radius=3.0, strength=2.0)
    # Repulsive pulse: Bottom right every 20s (0.05 Hz)
    if repulsive_pulse(t, freq=0.05):
        force += compute_repulsion_force(position, CORNERS["top_right"])
    # Appetitive pulse: Top left every 20s (0.05 Hz)
    if appetitive_pulse(t, freq=0.05):
        force += compute_attraction_force(position, CORNERS["top_right"], radius=3.0, strength=2.0)
    # Constant attraction: Bottom left (LiPS, r=2m)
    force += compute_attraction_force(position, CORNERS["bottom_left"], radius=5.0, strength=6.0)
    # Constant attraction: Bottom right (LiPS, r=2m)
    force += compute_attraction_force(position, CORNERS["top_right"], radius=5.0, strength=4.0)
    return force
   
   
def compute_quadrant_percentages(positions, dt=DT):
    """Return the percentage of time spent in each quadrant."""
    total = len(positions)
    quad_I   = (positions[:,0] > 0) & (positions[:,1] > 0)
    quad_II  = (positions[:,0] < 0) & (positions[:,1] > 0)
    quad_III = (positions[:,0] < 0) & (positions[:,1] < 0)
    quad_IV  = (positions[:,0] > 0) & (positions[:,1] < 0)
    return [
        100 * np.sum(quad_I)   / total,
        100 * np.sum(quad_II)  / total,
        100 * np.sum(quad_III) / total,
        100 * np.sum(quad_IV)  / total
    ]

def compute_quadrant_times(positions, dt=DT):
    """
    Calculate the time spent in each quadrant.

    :param positions: np.ndarray of shape (N, 2), trajectory positions.
    :param dt: Timestep duration in seconds.
    :return: dict with times in seconds for each quadrant.
    """
    quad_I   = (positions[:,0] > 0) & (positions[:,1] > 0)
    quad_II  = (positions[:,0] < 0) & (positions[:,1] > 0)
    quad_III = (positions[:,0] < 0) & (positions[:,1] < 0)
    quad_IV  = (positions[:,0] > 0) & (positions[:,1] < 0)

    n_I   = np.sum(quad_I)
    n_II  = np.sum(quad_II)
    n_III = np.sum(quad_III)
    n_IV  = np.sum(quad_IV)

    times = {
        "Quadrant I (upper right)":    n_I * dt,
        "Quadrant II (upper left)":    n_II * dt,
        "Quadrant III (lower left)":   n_III * dt,
        "Quadrant IV (lower right)":   n_IV * dt,
    }

    total_time = len(positions) * dt
    print("Time spent in each quadrant:")
    for k, v in times.items():
        print(f"  {k:26}: {v:.1f} s ({100*v/total_time:.1f}%)")
    return times


def retrofuturistic_data_log(positions, dt, subject_number=1):
    """Print and save a retrofuturistic data log with simplified stimuli info."""
    # Compute future date
    future_date = (datetime.date.today().replace(year=datetime.date.today().year + 200))
    date_str = future_date.strftime("%Y-%m-%d")

    # Quadrant calculation
    quad_times = compute_quadrant_times(positions, dt)
    quadrant_names = [
        "Quadrant I (upper right)",
        "Quadrant II (upper left)",
        "Quadrant III (lower left)",
        "Quadrant IV (lower right)"
    ]

    # Arena reference map
    stimulus_lines = [
        "  - Top Left (-10,  10): LED",
        "  - Top Right ( 10,  10): LED + LiPS",
        "  - Bottom Right ( 10, -10): Neutral",
        "  - Bottom Left (-10, -10): LiPS"
    ]

    header = (
        "++" + "="*82 + "++\n"
        "||" + " " * 82 + "||\n"
        "||          KESSLER PANORBITAL INDUSTRIES - BIO-MONITORING DIVISION                 ||\n"
        "||" + " " * 82 + "||\n"
        "||                 P A N O P T I C A M   B E H A V I O U R A L   S Y S T E M        ||\n"
        "||" + " " * 82 + "||\n"
        f"||   SESSION DATE: {date_str} {' ' * (64-len(date_str))}||\n"
        "||" + " " * 82 + "||\n"
        "++" + "="*82 + "++\n"
        "\nSYSTEM NOMENCLATURE:\n"
        "  - Species: 51U6-M\n"
        f"  - Subject: {subject_number}\n"
        "  - Data Stream: Position (X,Y), Quadrant\n\n"
        "COORDINATE SYSTEM REFERENCE:\n"
        "(Arena origin: (0,0), North=Top)\n\n"
        "STIMULUS LOCATIONS:\n"
    )

    header += "\n".join(stimulus_lines) + "\n"

    header += "\nQUADRANT OCCUPANCY:\n"
    for name in quadrant_names:
        t = quad_times[name]
        header += f"  - {name:26}: {t:.1f} s\n"

    header += (
        "\nBEGIN DATA LOG...\n"
        + "-"*100 + "\n"
        + "| Time (min) |   X (m)   |   Y (m)   | Quadrant | LED Wavelength (nm) |\n"
        + "-"*100 + "\n"
    )


    # Create data log table (downsample for brevity)
    step_skip = max(1, int(0.5 / dt))  # log every ~0.5s
    lines = []
    # Inside retrofuturistic_data_log() after "lines = []"
    for i in range(0, len(positions), step_skip):
        time_min = i * dt / 60.0
        x, y = positions[i]
        if x > 0 and y > 0:
            quad = "I"
        elif x < 0 and y > 0:
            quad = "II"
        elif x < 0 and y < 0:
            quad = "III"
        else:
            quad = "IV"
        # Wavelength cycles through list
        wavelength = LED_WAVELENGTHS[i % len(LED_WAVELENGTHS)]
        lines.append(f"| {time_min:10.4f} | {x:9.4f} | {y:9.4f} |   {quad:7} | {wavelength:7.1f} nm |")

    header += "\n".join(lines[:100])  # Limit to first 100 rows for visual sanity
    header += (
        "\n" + "-"*84 + "\n"
        f"LOG ENDED -- {len(lines)} rows, full data available as CSV.\n"
    )

    # Save log to file
    log_filename = f"subject_{subject_number}_log.txt"
    with open(log_filename, "w") as f:
        f.write(header)
    print(header)
    print(f"\nArena figure saved as subject_{subject_number}_arena.png")
    print(f"Retro data log saved as {log_filename}")



# --------- Main loop for all animals -----------
quad_table = []

future_date = (datetime.date.today().replace(year=datetime.date.today().year + 200))
date_str = future_date.strftime("%Y-%m-%d")

for animal in range(1, N_ANIMALS + 1):
    # --- Run the simulation ---
    positions, times = simulate_trajectory(seed=animal)
    quad_percents = compute_quadrant_percentages(positions, dt=DT)
    quad_table.append([animal] + quad_percents)

    # --- RETRO LOG ---
    retrofuturistic_data_log(positions, DT, subject_number=animal)

    # --- PNG ---
    plot_trajectory(positions, subject_number=animal)

    # --- CSV ---
    led_wavelengths = np.array([LED_WAVELENGTHS[i % len(LED_WAVELENGTHS)] for i in range(len(positions))])
    full_array = np.column_stack((positions, led_wavelengths))
    np.savetxt(f"subject_{animal}_trajectory.csv", full_array, delimiter=",", header="x,y,LED_wavelength_nm", comments='')


# --- Grand summary table for all animals ---
quad_table = np.array(quad_table)
mean_percents = np.mean(quad_table[:, 1:], axis=0)

header = (
    "++" + "="*70 + "++\n"
    "||" + " " * 70 + "||\n"
    "||      KESSLER PANORBITAL INDUSTRIES - BIO-MONITORING DIVISION        ||\n"
    "||" + " " * 70 + "||\n"
    "||             PANOPTICAM QUADRANT OCCUPANCY SUMMARY                   ||\n"
    "||" + " " * 70 + "||\n"
    f"||   SESSION DATE: {date_str}      SPECIES: {ANIMAL_SPECIES:<12}     ||\n"
    "||" + " " * 70 + "||\n"
    "++" + "="*70 + "++\n"
    "\nEXPERIMENTAL GROUP: 20 animals, simulated single session each\n\n"
    "QUADRANT DEFINITIONS (Centered Arena):\n"
    "  I   = (x > 0,  y > 0)   II  = (x < 0,  y > 0)\n"
    "  III = (x < 0,  y < 0)   IV  = (x > 0,  y < 0)\n"
    "\nSUMMARY TABLE:\n"
    "+--------+-----------+-----------+-----------+-----------+\n"
    "| Animal | Quad I %  | Quad II % | Quad III% | Quad IV % |\n"
    "+--------+-----------+-----------+-----------+-----------+"
)

body = ""
for row in quad_table:
    animal = int(row[0])
    q1, q2, q3, q4 = row[1:]
    body += f"\n|  {animal:2d}    |  {q1:8.2f} |  {q2:8.2f} |  {q3:8.2f} |  {q4:8.2f} |"
body += "\n+--------+-----------+-----------+-----------+-----------+"

mean_line = (
    f"\n|  MEAN  |  {mean_percents[0]:8.2f} |  {mean_percents[1]:8.2f} |"
    f"  {mean_percents[2]:8.2f} |  {mean_percents[3]:8.2f} |"
    "\n+--------+-----------+-----------+-----------+-----------+"
)

table_txt = header + body + mean_line
summary_file = f"panopticam_quadrant_summary_{ANIMAL_SPECIES}.txt"
with open(summary_file, "w") as f:
    f.write(table_txt)

print(table_txt)
print("\nMEAN OCCUPANCY (%):")
print(f"  Quadrant I   : {mean_percents[0]:.2f}%")
print(f"  Quadrant II  : {mean_percents[1]:.2f}%")
print(f"  Quadrant III : {mean_percents[2]:.2f}%")
print(f"  Quadrant IV  : {mean_percents[3]:.2f}%")
print(f"\nSummary written to {summary_file}")