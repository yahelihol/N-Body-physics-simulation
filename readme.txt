
See image

Gravitational Motion Sim – Pygame

Simulation of gravitational interaction and orbital motion in Pygame.
Objects attract each other, collide, bounce, and leave trails.
For fun or basic physics visualization.

Features:
- Multiple colored bodies (4 by default), randomly placed with random motion.
- Real-time gravitational pull between all objects.
- Optional collisions (toggle in code) with bouncy response.
- Smooth zoom and panning with mouse.
- Trails show motion history; vector arrows show current velocity.
- Red dot = center of mass; red arrow = total momentum vector.
- Adjustable sliders for:
- - Gravitational constant G
- - Air resistance AR

Controls:
Drag (left-click): pan view.
Mouse wheel (if added): zoom in/out.
Mouse hover: shows world coordinates under cursor.
Sliders: tweak gravity and air resistance on the fly.

Notes:
Collision behavior can be toggled with the collide flag in the code.
Slower machines may lag if you add too many objects or increase G too much.
No unit system—just abstract simulation.


Try tweaking object count, initial velocities, and G to see different orbits and chaos.
maybe one day this will be 3D, or use general relativity
