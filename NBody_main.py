import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circles Orbiting Each Other")

# Colors
WHITE = (255, 255, 255)
GRID_COLOR = (200, 200, 200)  # Light gray grid color
TEXT_COLOR = (0, 0, 0)  # Black for the mouse position text

SLIDER_COLOR = (100, 100, 100)
SLIDER_HANDLE_COLOR = (55, 55, 55)


# Circle properties
circle_radius = 20
N = 4  # Number of circles

# Constants
G = 0.1  # Gravitational constant
AIR_RESISTANCE = 1 # Air resistance factor
MAX_PATH_LENGTH = 600  # Limit the length of the trail
damping = 1
collide = False

paused = False


# Slider class
class Slider:
    def __init__(self, x, y, width, min_value, max_value, step_size, initial_value):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_value = min_value
        self.max_value = max_value + step_size
        self.step_size = step_size
        self.value = self._snap_to_step(initial_value)
        self.handle_rect = pygame.Rect(x + (self.value - self.min_value) / (self.max_value - self.min_value) * width - 10, y - 5, 20, 30)
        self.dragging = False

    def _snap_to_step(self, value):
        """Snap the value to the nearest step."""
        return round((value - self.min_value) / self.step_size) * self.step_size + self.min_value

    def draw(self, screen):
        pygame.draw.rect(screen, SLIDER_COLOR, self.rect)
        pygame.draw.rect(screen, SLIDER_HANDLE_COLOR, self.handle_rect)


    def update(self, mouse_pos, mouse_pressed):
        if self.dragging:
            self.handle_rect.centerx = mouse_pos[0]
            if self.handle_rect.left < self.rect.left:
                self.handle_rect.left = self.rect.left
            if self.handle_rect.right > self.rect.right:
                self.handle_rect.right = self.rect.right
            self.value = self._snap_to_step(self.min_value + (self.handle_rect.centerx - self.rect.left) / self.rect.width * (self.max_value - self.min_value))

        if self.handle_rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.dragging = True
        elif not mouse_pressed[0]:
            self.dragging = False

    def get_value(self):
        return self.value


# Circle class
class Circle:
    def __init__(self, pos, velocity, color):
        self.pos = pos
        self.velocity = velocity
        self.color = color
        self.path = []

    def update_position(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.path.append((self.pos[0], self.pos[1]))
        if len(self.path) > MAX_PATH_LENGTH:
            self.path.pop(0)

    def draw_path(self, screen, zoom, offset):
        # Loop through the path and draw fading circles
        for i, point in enumerate(self.path):
            # Calculate alpha based on the point's age
            alpha = int(255 * (i / len(self.path)))  # Fades from 0 to 255
            fade_color = (*self.color, alpha)  # Add alpha to the color

            # Create a surface with per-pixel alpha for drawing the trail with transparency
            trail_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, fade_color, (2, 2), 2)

            # Calculate the zoomed position for the point
            point_zoomed = (int((point[0] - offset[0]) * zoom), int((point[1] - offset[1]) * zoom))

            # Blit the transparent trail point onto the screen
            screen.blit(trail_surface, (point_zoomed[0] - 2, point_zoomed[1] - 2))

    def draw(self, screen, zoom, offset):
        pos_zoomed = (int((self.pos[0] - offset[0]) * zoom), int((self.pos[1] - offset[1]) * zoom))
        radius_zoomed = int(circle_radius * zoom)
        pygame.draw.circle(screen, self.color, pos_zoomed, radius_zoomed)

    def draw_velocity(self, screen, zoom, offset):
        # Calculate the end point of the velocity vector
        start_pos = (int((self.pos[0] - offset[0]) * zoom), int((self.pos[1] - offset[1]) * zoom))
        end_pos = (int(start_pos[0] + self.velocity[0] * 10 * zoom), int(start_pos[1] + self.velocity[1] * 10 * zoom))

        # Draw the velocity vector
        pygame.draw.line(screen, self.color, start_pos, end_pos, 2)

        # Draw the arrowhead
        arrow_length = 10 * zoom
        angle = math.atan2(self.velocity[1], self.velocity[0])
        arrowhead = [
            (end_pos[0] - arrow_length * math.cos(angle - math.pi / 6),
             end_pos[1] - arrow_length * math.sin(angle - math.pi / 6)),
            (end_pos[0] - arrow_length * math.cos(angle + math.pi / 6),
             end_pos[1] - arrow_length * math.sin(angle + math.pi / 6)),
            end_pos
        ]
        pygame.draw.polygon(screen, self.color, arrowhead)

def detect_collision(circle1, circle2):
    dx = circle1.pos[0] - circle2.pos[0]
    dy = circle1.pos[1] - circle2.pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    return distance <= 2 * circle_radius  # Collision happens when distance is less than or equal to the sum of radii

def resolve_collision(circle1, circle2):
    if not collide:
        return
    # Calculate the vector between the two circle centers
    dx = circle1.pos[0] - circle2.pos[0]
    dy = circle1.pos[1] - circle2.pos[1]
    distance = math.sqrt(dx**2 + dy**2)

    if distance == 0:  # Prevent division by zero in case circles overlap perfectly
        distance = 1

    # Normalized direction of collision (line of impact)
    nx = dx / distance
    ny = dy / distance

    # Resolve overlap by moving the circles apart based on their overlap distance
    overlap = 2 * circle_radius - distance
    if overlap > 0:
        move_dist = overlap / 2
        circle1.pos[0] += nx * move_dist
        circle1.pos[1] += ny * move_dist
        circle2.pos[0] -= nx * move_dist
        circle2.pos[1] -= ny * move_dist

    # Relative velocity in the direction of the collision
    dvx = circle1.velocity[0] - circle2.velocity[0]
    dvy = circle1.velocity[1] - circle2.velocity[1]

    # Velocity along the collision normal (dot product of relative velocity and normal)
    vn = dvx * nx + dvy * ny

    # If vn is greater than 0, the circles are moving apart, so no need to resolve the collision
    if vn > 0:
        return

    # Calculate impulse scalar with a damping factor to prevent too "bouncy" collisions
    impulse = (2 * vn) / (1 + 1)  # Assuming equal mass for both circles
    impulse *= damping  # Apply damping to reduce the intensity of the collision

    # Apply impulse to both circles (in the direction of the collision normal)
    circle1.velocity[0] -= impulse * nx
    circle1.velocity[1] -= impulse * ny
    circle2.velocity[0] += impulse * nx
    circle2.velocity[1] += impulse * ny


# Initialize circles
circles = []
for i in range(N):
    pos = [random.randint(-int(WIDTH/3), int(WIDTH/3)), random.randint(-int(HEIGHT/3), int(HEIGHT/3))]
    velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
    color = [random.randint(50, 255) for _ in range(3)]
    circles.append(Circle(pos, velocity, color))


def calculate_gravitational_force(pos1, pos2):
    distance_x = pos2[0] - pos1[0]
    distance_y = pos2[1] - pos1[1]
    distance = math.sqrt(distance_x ** 2 + distance_y ** 2)
    if distance == 0:
        distance = 1
    force_x = (distance_x / distance) * G
    force_y = (distance_y / distance) * G
    return force_x, force_y


def calculate_center_of_mass(circles):
    total_x = 0
    total_y = 0
    total_mass = len(circles)  # Assuming all circles have the same mass

    for circle in circles:
        total_x += circle.pos[0]
        total_y += circle.pos[1]

    # Calculate the average position (center of mass)
    center_of_mass_x = total_x / total_mass
    center_of_mass_y = total_y / total_mass

    return (center_of_mass_x, center_of_mass_y)

def draw_center_of_mass(screen, center_of_mass, zoom, offset):
    # Convert the center of mass position to screen coordinates
    center_of_mass_screen_x = int((center_of_mass[0] - offset[0]) * zoom)
    center_of_mass_screen_y = int((center_of_mass[1] - offset[1]) * zoom)

    # Draw the center of mass as a red circle on the screen
    pygame.draw.circle(screen, (255, 0, 0), (center_of_mass_screen_x, center_of_mass_screen_y), 5)


# Function to draw the grid
def draw_grid(screen, zoom, offset, grid_spacing=50):
    """Draws a grid that scales with zoom and moves with panning."""
    spacing = grid_spacing * zoom  # Scale the grid spacing by the zoom level

    # Calculate the starting points for the grid, based on the offset
    start_x = -offset[0] * zoom % spacing
    start_y = -offset[1] * zoom % spacing

    # Draw vertical lines
    for x in range(int(start_x), WIDTH, int(spacing)):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))

    # Draw horizontal lines
    for y in range(int(start_y), HEIGHT, int(spacing)):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

def draw_velocity_sum(screen, circles, zoom, offset, point):
    # Calculate the middle point of the screen in world coordinates
    middle_point = point  # [WIDTH / 2 / zoom + offset[0], HEIGHT / 2 / zoom + offset[1]]

    # Initialize total velocity vector
    total_velocity = [0, 0]

    # Draw each velocity vector and add it to the total velocity vector
    current_start = middle_point
    for circle in circles:
        # Calculate the end point of the current velocity vector in world coordinates
        end_pos_world = [current_start[0] + circle.velocity[0] * 10, current_start[1] + circle.velocity[1] * 10]

        # Convert both start and end points to screen coordinates
        start_pos_screen = (int((current_start[0] - offset[0]) * zoom), int((current_start[1] - offset[1]) * zoom))
        end_pos_screen = (int((end_pos_world[0] - offset[0]) * zoom), int((end_pos_world[1] - offset[1]) * zoom))

        # Draw the current velocity vector
        pygame.draw.line(screen, circle.color, start_pos_screen, end_pos_screen, 2)

        # Calculate the angle of the velocity vector for the arrowhead
        angle = math.atan2(circle.velocity[1], circle.velocity[0])

        # Length of the arrowhead in screen coordinates
        arrow_length = 10 * zoom

        # Compute the two points for the arrowhead, using the angle
        arrowhead_left = (end_pos_screen[0] - arrow_length * math.cos(angle - math.pi / 6),
                          end_pos_screen[1] - arrow_length * math.sin(angle - math.pi / 6))
        arrowhead_right = (end_pos_screen[0] - arrow_length * math.cos(angle + math.pi / 6),
                           end_pos_screen[1] - arrow_length * math.sin(angle + math.pi / 6))

        # Draw the arrowhead using the calculated points
        pygame.draw.polygon(screen, circle.color, [arrowhead_left, arrowhead_right, end_pos_screen])

        # Update the total velocity vector
        total_velocity[0] += circle.velocity[0]
        total_velocity[1] += circle.velocity[1]

        # Update the start point for the next vector
        current_start = end_pos_world

    # Draw the total velocity vector in the same manner
    end_pos_total_world = [middle_point[0] + total_velocity[0] * 10, middle_point[1] + total_velocity[1] * 10]
    end_pos_total_screen = (int((end_pos_total_world[0] - offset[0]) * zoom), int((end_pos_total_world[1] - offset[1]) * zoom))
    middle_point_screen = (int((middle_point[0] - offset[0]) * zoom), int((middle_point[1] - offset[1]) * zoom))

    if end_pos_total_screen != middle_point_screen:
        pygame.draw.line(screen, (255, 0, 0), middle_point_screen, end_pos_total_screen, 2)

        # Draw the arrowhead for the total velocity vector
        arrow_length = 10 * zoom
        total_angle = math.atan2(total_velocity[1], total_velocity[0])
        arrowhead_left = (end_pos_total_screen[0] - arrow_length * math.cos(total_angle - math.pi / 6),
                          end_pos_total_screen[1] - arrow_length * math.sin(total_angle - math.pi / 6))
        arrowhead_right = (end_pos_total_screen[0] - arrow_length * math.cos(total_angle + math.pi / 6),
                           end_pos_total_screen[1] - arrow_length * math.sin(total_angle + math.pi / 6))
        pygame.draw.polygon(screen, (255, 0, 0), [arrowhead_left, arrowhead_right, end_pos_total_screen])



# Slider initialization
g_slider = Slider(20, HEIGHT - 60, 200, -0.2, 1.2, 0.1, G)
air_resistance_slider = Slider(20, HEIGHT - 30, 200, 0.8, 1.05, 0.01, AIR_RESISTANCE)

# Camera zoom level and offset
zoom = 1.0
zoom_speed = 0.1
offset = [-WIDTH/2, -HEIGHT/2]
panning = False
prev_mouse_pos = (0, 0)

# Font for displaying mouse position
font = pygame.font.Font(None, 24)  # You can change font size if needed

# Clock to control frame rate
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    screen.fill(WHITE)

    # Draw the grid first
    draw_grid(screen, zoom, offset)

    if not paused:
        # Calculate gravitational forces and update velocities
        for i in range(N):
            for j in range(i + 1, N):
                force_x, force_y = calculate_gravitational_force(circles[i].pos, circles[j].pos)
                circles[i].velocity[0] += force_x
                circles[i].velocity[1] += force_y
                circles[j].velocity[0] -= force_x
                circles[j].velocity[1] -= force_y

        for i in range(N):
            for j in range(i + 1, N):
                if detect_collision(circles[i], circles[j]):
                    resolve_collision(circles[i], circles[j])

        # Update each circle's position and apply air resistance
        for circle in circles:
            circle.velocity[0] *= AIR_RESISTANCE
            circle.velocity[1] *= AIR_RESISTANCE
            circle.update_position()

    # Draw all paths first
    for circle in circles:
        circle.draw_path(screen, zoom, offset)

    # Draw all circles and velocity arrows
    for circle in circles:
        circle.draw(screen, zoom, offset)
        circle.draw_velocity(screen, zoom, offset)

    # Calculate and draw the center of mass
    center_of_mass = calculate_center_of_mass(circles)
    draw_center_of_mass(screen, center_of_mass, zoom, offset)

    draw_velocity_sum(screen, circles, zoom, offset, center_of_mass)

    # Display mouse position near the cursor
    mouse_pos = pygame.mouse.get_pos()
    world_mouse_x = int(mouse_pos[0] / zoom + offset[0])
    world_mouse_y = int(mouse_pos[1] / zoom + offset[1])
    mouse_text = f"({world_mouse_x}, {world_mouse_y})"
    text_surface = font.render(mouse_text, True, TEXT_COLOR)
    screen.blit(text_surface, (mouse_pos[0] + 10, mouse_pos[1] + 10))  # Draw the text near the mouse

    zoom_text = f"zoom: {round(zoom, 3)}"
    text_surface = font.render(zoom_text, True, TEXT_COLOR)
    screen.blit(text_surface, (10, 10))
    G_text = f"G: {round(G, 3)}"
    text_surface = font.render(G_text, True, TEXT_COLOR)
    screen.blit(text_surface, (230, 542))
    AIR_RESISTANCE_text = f"AR: {round(AIR_RESISTANCE, 3)}"
    text_surface = font.render(AIR_RESISTANCE_text, True, TEXT_COLOR)
    screen.blit(text_surface, (230, 572))
    if paused:
        pause_text = "PAUSED"
        text_surface = font.render(pause_text, True, TEXT_COLOR)
        screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT // 2))

    mouse_pressed = pygame.mouse.get_pressed()

    g_slider.update(mouse_pos, mouse_pressed)
    air_resistance_slider.update(mouse_pos, mouse_pressed)
    g_slider.draw(screen)
    air_resistance_slider.draw(screen)
    AIR_RESISTANCE = air_resistance_slider.value
    G = g_slider.value

    if g_slider.dragging or air_resistance_slider.dragging:
        slider_being_used = True
    else:
        slider_being_used = False

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                panning = True
                prev_mouse_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                panning = False
        elif event.type == pygame.MOUSEMOTION:
            if panning and not slider_being_used:
                current_mouse_pos = pygame.mouse.get_pos()
                offset[0] -= (current_mouse_pos[0] - prev_mouse_pos[0]) / zoom
                offset[1] -= (current_mouse_pos[1] - prev_mouse_pos[1]) / zoom
                prev_mouse_pos = current_mouse_pos
        elif event.type == pygame.MOUSEWHEEL:
            current_mouse_pos = pygame.mouse.get_pos()
            offset[0] += (current_mouse_pos[0]) / zoom
            offset[1] += (current_mouse_pos[1]) / zoom
            zoom_change = event.y * zoom_speed
            zoom = round(max(0.1, zoom + zoom_change),3)
            offset[0] -= (current_mouse_pos[0]) / zoom
            offset[1] -= (current_mouse_pos[1]) / zoom
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_UP:
                G = round(G+0.01, 3)
            elif event.key == pygame.K_DOWN:
                G = round(G-0.01, 3)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_f]:
        offset[0] = center_of_mass[0] - WIDTH / 2 / zoom
        offset[1] = center_of_mass[1] - HEIGHT / 2 / zoom



    pygame.display.flip()
    clock.tick(60)

pygame.quit()