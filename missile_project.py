import os
import sys
import math
import random

# Linux context fix
os.environ['PYOPENGL_PLATFORM'] = 'glx'

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Animation & State Variables ---
anim_state = -1  
anim_t = 0.0    
blast_radius = 0.0
selected_country = "None (Type name & press Enter)"
intro_angle = 0.0 

# NEW: Typing variable
typed_input = ""

# Countdown variables
total_countdown = 7.0 
countdown = total_countdown

# Crater Persistence variables (Dynamic ground deformation)
crater_radius = 0.0
crater_depth = 0.0

missile_speed = 0.002
speed_display = 1.0 

missile_pos = [0.0, 2.0, 150.0] 
P3 = [0.0, -150.0]  

target_locations = {
    '1': {'name': 'USA', 'coord': [0.0, -150.0]},
    '2': {'name': 'China', 'coord': [60.0, -130.0]},
    '3': {'name': 'Russia', 'coord': [-60.0, -160.0]},
    '4': {'name': 'India', 'coord': [110.0, -100.0]},
    '5': {'name': 'Germany', 'coord': [-100.0, -90.0]},
    '6': {'name': 'Japan', 'coord': [150.0, -140.0]},
    '7': {'name': 'Israel', 'coord': [-160.0, -180.0]},
    '8': {'name': 'Canada', 'coord': [40.0, -210.0]},
    '9': {'name': 'Australia', 'coord': [-40.0, -220.0]},
    '0': {'name': 'UK', 'coord': [90.0, -230.0]}
}

stars = [(random.uniform(-300, 300), random.uniform(50, 200), random.uniform(-300, 300)) for _ in range(800)]
random.seed(42)

# Generate Dynamic Terrain Grid
terrain_grid = {}
for z in range(-320, 320, 10):
    for x in range(-320, 320, 10):
        terrain_grid[(x, z)] = random.uniform(-0.6, 0.6) # Natural noise

city_blocks = []
def init_city_blocks():
    global city_blocks
    city_blocks.clear()
    for key, loc in target_locations.items():
        tx, tz = loc['coord']
        for _ in range(18):
            bx = tx + random.uniform(-25, 25)
            bz = tz + random.uniform(-25, 25)
            bw = random.uniform(2.0, 5.0)
            bh = random.uniform(5.0, 20.0) 
            cr = random.uniform(0.5, 0.8) 
            rot = random.uniform(0, 90)
            city_blocks.append([bx, bz, bw, bh, cr, rot])

init_city_blocks()

city_lights = []
for key, loc in target_locations.items():
    tx, tz = loc['coord']
    for _ in range(250):
        city_lights.append([tx + random.gauss(0, 3.0), tz + random.gauss(0, 3.0), random.uniform(0.7, 1.0), True])
    for _ in range(150):
        city_lights.append([tx + random.gauss(0, 10.0), tz + random.gauss(0, 10.0), random.uniform(0.2, 0.6), False])

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    light_pos = [0.0, 200.0, 0.0, 1.0] 
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.05, 0.05, 0.08, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.4, 0.4, 0.5, 1.0])
    glClearColor(0.005, 0.01, 0.03, 1.0) 

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glEnable(GL_LIGHTING)

def draw_holographic_globe():
    glPushMatrix()
    glDisable(GL_LIGHTING)
    glColor4f(0.0, 0.1, 0.2, 0.9)
    glutSolidSphere(40.0, 50, 50)
    glColor4f(0.0, 0.5, 0.8, 0.4)
    glutWireSphere(40.5, 25, 25)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_launch_pad():
    glPushMatrix()
    glTranslatef(0.0, 0.1, 150.0)
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glScalef(15.0, 0.5, 15.0)
    glutSolidCube(1.0)
    glPopMatrix()
    glColor3f(0.5, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(4.0, 8.0, 0.0)
    glScalef(1.0, 16.0, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    glPopMatrix()

def draw_satellite_map():
    glPushMatrix()
    
    # --- PERFECTED: True Dynamic 3D Ground Deformation (Crater) ---
    grid_step = 10
    for z in range(-300, 300, grid_step):
        glBegin(GL_TRIANGLE_STRIP)
        for x in range(-300, 310, grid_step):
            for dz in [0, grid_step]:
                cz = z + dz
                base_y = terrain_grid.get((x, cz), 0.0)
                y = base_y
                r, g, b_col = 0.02, 0.05, 0.03 # Base terrain color

                if crater_radius > 0:
                    dist = math.sqrt((x - P3[0])**2 + (cz - P3[1])**2)
                    if dist <= crater_radius * 1.3:
                        nd = dist / crater_radius
                        if nd <= 1.0:
                            # Crater Bowl (Goes Deep)
                            y = base_y - crater_depth * math.cos(nd * math.pi / 2)
                            glow = (1.0 - nd) ** 1.5
                            # Magma/Burn effect
                            r = 0.1 + glow * 0.9
                            g = 0.02 + glow * 0.4
                            b_col = 0.03
                        else:
                            # Crater Rim (Pushed Upwards)
                            rim_nd = (nd - 1.0) / 0.3
                            y = base_y + (crater_depth * 0.4) * math.sin(rim_nd * math.pi)
                            r = 0.15; g = 0.1; b_col = 0.05

                glColor3f(r, g, b_col)
                glNormal3f(0.0, 1.0, 0.0)
                glVertex3f(x, y, cz)
        glEnd()
    # --------------------------------------------------------------

    glDisable(GL_LIGHTING)
    glPointSize(2.0)
    glBegin(GL_POINTS)
    for lx, lz, b, is_core in city_lights:
        # Hide lights if they fall into the blast zone
        if crater_radius > 0 and math.sqrt((lx - P3[0])**2 + (lz - P3[1])**2) < crater_radius:
            continue
        if is_core: glColor4f(1.0, 0.9, 0.6, b) 
        else: glColor4f(1.0, 0.6, 0.2, b) 
        glVertex3f(lx, 0.1, lz)
    glEnd()
    glEnable(GL_LIGHTING)

    for bx, bz, bw, bh, cr, rot in city_blocks:
        if bh <= 0.0: continue # Skip rendering fully destroyed buildings
        glPushMatrix()
        glTranslatef(bx, bh/2.0, bz)
        glRotatef(rot, 0, 1, 0)
        glColor3f(cr, cr, cr + 0.05) 
        glScalef(bw, bh, bw)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()

def draw_modern_missile():
    glPushMatrix()
    glScalef(2.5, 2.5, 2.5) 
    
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    glRotatef(-90, 1, 0, 0)
    
    # --- BANGLADESH FLAG DESIGN ---
    glColor3f(0.0, 0.42, 0.24)
    gluCylinder(quadric, 0.4, 0.4, 1.3, 32, 32)
    
    glPushMatrix()
    glTranslatef(0.0, 0.0, 1.3)
    glColor3f(0.86, 0.08, 0.24)
    gluCylinder(quadric, 0.4, 0.4, 0.9, 32, 32)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0.0, 0.0, 2.2)
    glColor3f(0.0, 0.42, 0.24)
    gluCylinder(quadric, 0.4, 0.4, 1.3, 32, 32)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, 0.0, 3.5)
    glColor3f(0.0, 0.42, 0.24)
    gluCylinder(quadric, 0.4, 0.0, 1.2, 32, 32)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0.0, 0.0, -0.5)
    glColor3f(0.1, 0.1, 0.1)
    gluCylinder(quadric, 0.3, 0.4, 0.5, 32, 32)
    glPopMatrix()
    
    glColor3f(0.86, 0.08, 0.24)
    for angle in [0, 90, 180, 270]:
        glPushMatrix()
        glRotatef(angle, 0, 0, 1)
        glBegin(GL_QUADS)
        glVertex3f(0.4, 0.0, 0.2)
        glVertex3f(1.2, 0.0, -0.2)
        glVertex3f(1.2, 0.0, 0.8)
        glVertex3f(0.4, 0.0, 1.5)
        glEnd()
        glPopMatrix()
    # ------------------------------

    # Engine Fire & Progressive Smoke
    if anim_state >= 0.5 and anim_state < 2:
        glDisable(GL_LIGHTING)
        f = random.uniform(0.9, 1.4)
        intensity = 1.0 
        
        if anim_state == 0.5:
            intensity = max(0.0, (total_countdown - countdown) / total_countdown)
            f *= (0.1 + 0.9 * intensity) 
        
        glPushMatrix(); glTranslatef(0.0, 0.0, -0.6); glRotatef(180, 1, 0, 0)
        glColor4f(1.0, 0.5, 0.0, 0.9); glutSolidCone(0.8*f, 5.0*f, 20, 20) 
        glColor4f(1.0, 1.0, 0.5, 1.0); glutSolidCone(0.4*f, 2.5*f, 20, 20) 
        glPopMatrix()
        
        if anim_state == 0.5 and intensity > 0.1:
            glColor4f(0.5, 0.5, 0.5, 0.8 * intensity) 
            num_smoke = int(2 + 15 * intensity) 
            for _ in range(num_smoke):
                glPushMatrix()
                spread = 1.0 + 4.0 * intensity 
                y_rise = random.uniform(-1, 2) * intensity
                glTranslatef(random.uniform(-spread, spread), y_rise, random.uniform(-spread, spread))
                glutSolidSphere(random.uniform(1.0, 1.5 + 2.5 * intensity), 10, 10)
                glPopMatrix()
                
        glEnable(GL_LIGHTING)
        
    gluDeleteQuadric(quadric)
    glPopMatrix()

def get_bezier_point_3d(t):
    u = 1.0 - t
    tt = t * t; uu = u * u; uuu = uu * u; ttt = tt * t
    P0 = [0.0, 2.0, 150.0]        
    P1 = [0.0, 250.0, 50.0]       
    P2 = [P3[0], 250.0, P3[1]+50] 
    P3_3d = [P3[0], 0.0, P3[1]]  
    x = uuu*P0[0] + 3*uu*t*P1[0] + 3*u*tt*P2[0] + ttt*P3_3d[0]
    y = uuu*P0[1] + 3*uu*t*P1[1] + 3*u*tt*P2[1] + ttt*P3_3d[1]
    z = uuu*P0[2] + 3*uu*t*P1[2] + 3*u*tt*P2[2] + ttt*P3_3d[2]
    return [x, y, z]

def cinematic_camera():
    if anim_state == -1:
        cam_x = math.sin(intro_angle) * 120.0
        cam_z = math.cos(intro_angle) * 120.0
        gluLookAt(cam_x, 60.0, cam_z,   0.0, 0.0, 0.0,   0.0, 1.0, 0.0)
    elif anim_state == 0:
        gluLookAt(0.0, 180.0, 180.0,   0.0, 0.0, -80.0,   0.0, 1.0, 0.0)
    elif anim_state == 0.5:
        gluLookAt(-15.0, 10.0, 175.0,   0.0, 5.0, 150.0,   0.0, 1.0, 0.0)
    elif anim_state == 1:
        cam_x = missile_pos[0] + 15.0  
        cam_y = missile_pos[1] + 10.0  
        cam_z = missile_pos[2] + 20.0 
        gluLookAt(cam_x, cam_y, cam_z,   missile_pos[0], missile_pos[1], missile_pos[2],   0.0, 1.0, 0.0)
    else:
        gluLookAt(P3[0] + 40.0, 25.0, P3[1] + 50.0,  P3[0], 0.0, P3[1],  0.0, 1.0, 0.0)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(55.0, 1.33, 0.1, 1000.0) 
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    
    cinematic_camera()
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0); glPointSize(1.5); glBegin(GL_POINTS)
    for star in stars: glVertex3f(star[0], star[1], star[2])
    glEnd(); glEnable(GL_LIGHTING)
    
    if anim_state == -1:
        draw_holographic_globe()
    else:
        draw_satellite_map()
        draw_launch_pad()
        
        if anim_state <= 1:
            glPushMatrix()
            glTranslatef(missile_pos[0], missile_pos[1], missile_pos[2])
            if anim_state == 1:
                next_pos = get_bezier_point_3d(min(anim_t+0.01, 1.0))
                dx = next_pos[0] - missile_pos[0]; dy = next_pos[1] - missile_pos[1]; dz = next_pos[2] - missile_pos[2]
                yaw = math.degrees(math.atan2(dx, dz))
                pitch = math.degrees(math.atan2(math.sqrt(dx*dx + dz*dz), dy))
                glRotatef(yaw, 0, 1, 0); glRotatef(pitch, 1, 0, 0)
            draw_modern_missile()
            glPopMatrix()
            
        elif anim_state == 2:
            glPushMatrix()
            glTranslatef(P3[0], 1.0, P3[1]); glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.2, 0.0, 0.8); glutSolidSphere(blast_radius, 40, 40)
            glColor4f(1.0, 0.9, 0.2, 0.9); glutSolidSphere(blast_radius*0.6, 30, 30)
            glColor3f(1.0, 1.0, 1.0); glutSolidSphere(blast_radius*0.3, 20, 20)
            glEnable(GL_LIGHTING); glPopMatrix()

    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 700)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    if anim_state == -1:
        draw_text(350, 350, "GLOBAL STRATEGIC COMMAND", GLUT_BITMAP_HELVETICA_18)
    elif anim_state == 0.5:
        draw_text(400, 350, f"IGNITION IN: {max(0, countdown):.1f}", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(420, 320, "SYSTEMS ONLINE...", GLUT_BITMAP_HELVETICA_18)
    else:
        draw_text(20, 670, f"TARGET: {selected_country}")
        
        # --- NEW TYPING UI ---
        if anim_state == 0:
            draw_text(20, 640, f"TYPE INPUT: {typed_input}_ (Press Enter to set)")
            draw_text(20, 610, f"SPEED: {speed_display:.2f}x (+/-)")
        else:
            draw_text(20, 640, f"SPEED: {speed_display:.2f}x (+/-)")
        
        draw_text(800, 670, "--- TARGET SECTORS ---")
        y_pos = 645
        for key in "1234567890":
            city_name = target_locations[key]['name']
            draw_text(800, y_pos, f"- {city_name}") # Removed the numbers
            y_pos -= 22
            
        if anim_state == 1:
            draw_text(20, 580, f"ALTITUDE: {int(missile_pos[1]*100)}m")
            draw_text(20, 550, f"DISTANCE: {int((1.0-anim_t)*1000)}km") 
        elif anim_state >= 2:
            draw_text(400, 650, "TARGET NEUTRALIZED", GLUT_BITMAP_TIMES_ROMAN_24)
            draw_text(430, 620, "Right Click to Reset")
        
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW); glPopMatrix()
    
    glutSwapBuffers()

def update(v):
    global anim_t, anim_state, missile_pos, blast_radius, intro_angle, countdown, city_blocks, crater_radius, crater_depth
    
    if anim_state == -1:
        intro_angle += 0.005 
        
    elif anim_state == 0.5:
        countdown -= 0.016 
        if countdown <= 0:
            anim_state = 1 
            
    elif anim_state == 1:
        anim_t += missile_speed 
        if anim_t >= 1.0: 
            anim_t = 1.0
            anim_state = 2
        missile_pos = get_bezier_point_3d(anim_t)
        
    elif anim_state == 2:
        blast_radius += 2.0 
        crater_radius = blast_radius 
        if crater_depth < 15.0:      
            crater_depth += 0.5
            
        for b in city_blocks: 
            dist = math.sqrt((b[0]-P3[0])**2 + (b[1]-P3[1])**2)
            if dist < blast_radius + 5.0 and b[3] > 0.0:
                b[3] -= 1.5 
                if b[3] < 0: b[3] = 0.0 # Flattens building to the ground
                
        if blast_radius > 60.0: anim_state = 3
        
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

# --- KEYBOARD FUNCTION WITH TYPING ADDED ---
def keyboard(key, x, y):
    global P3, selected_country, missile_speed, speed_display, typed_input
    
    try:
        k = key.decode("utf-8")
    except UnicodeDecodeError:
        return
    
    if anim_state == 0: 
        if k == '\r' or k == '\n': # ENTER KEY PRESSED
            for _, city in target_locations.items():
                if city['name'].lower() == typed_input.strip().lower():
                    P3 = city['coord']
                    selected_country = city['name']
                    break
            typed_input = "" # Clear after enter
            
        elif k == '\x08' or k == '\x7f': # BACKSPACE
            typed_input = typed_input[:-1]
            
        elif k == '+' or k == '=':
            missile_speed += 0.0005; speed_display += 0.25
            
        elif k == '-':
            if missile_speed > 0.0005: 
                missile_speed -= 0.0005; speed_display -= 0.25
                
        elif k.isprintable(): # ANY OTHER LETTER
            typed_input += k

def mouse(btn, state, x, y):
    global anim_state, anim_t, blast_radius, missile_pos, countdown, crater_radius, crater_depth, typed_input, selected_country
    if state == GLUT_DOWN:
        if anim_state == -1 and btn == GLUT_LEFT_BUTTON:
            anim_state = 0
            typed_input = ""
        elif btn == GLUT_LEFT_BUTTON and anim_state == 0 and selected_country != "None (Type name & press Enter)":
            anim_state = 0.5 
            countdown = total_countdown 
        elif btn == GLUT_RIGHT_BUTTON:
            # RESET EVERYTHING
            anim_state = -1; anim_t = 0.0; blast_radius = 0.0; missile_pos = [0.0, 2.0, 150.0]
            crater_radius = 0.0; crater_depth = 0.0 
            selected_country = "None (Type name & press Enter)"
            typed_input = ""
            init_city_blocks()

def main():
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 700); glutCreateWindow(b"Full Cinematic ICBM Simulator (True Crater Deformation)")
    init_gl()
    glutDisplayFunc(display); glutTimerFunc(16, update, 0)
    glutKeyboardFunc(keyboard); glutMouseFunc(mouse)
    glutMainLoop()

if __name__ == "__main__":
    main()