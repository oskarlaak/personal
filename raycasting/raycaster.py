# Main TODOs:
# Interception type (horizontal/vertical) could be determined faster without manually comparing squared distances
# Make FPS counter show other variables aswell such as player position and viewangle
# Simple wall texturing if everything else done (for example black lines surrounding the walls/blocks)

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# Collisions are still not 100% working

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

D_W = 1920
D_H = 1080
FOV = 1.4  # 1.4 radians == about 80 degrees
RAYS = 240  # Drawing frequency across the screen / Rays casted each frame ; D_W / RAYS should always be int
VIEWANGLE = 0.11  # Any starting VIEWANGLE parallel with a gridline will run into errors
SENSITIVITY = 0.003

PLAYER_X = 10
PLAYER_Y = 17
PLAYER_SPEED = 0.15  # Must be <= HITBOX_HALFSIZE
HITBOX_HALFSIZE = 0.2  # Player's hitbox halfsize

WALL_DATA = []

# Assigning colours to tilemap indexes
COLOURS = {
    1: (12 ,123, 32),
    2: (123,23 , 19),
    3: (234,3  ,255)
}

# Pygame stuff
pygame.init()
pygame.display.set_caption('Raycaster')
GAMEDISPLAY = pygame.display.set_mode((D_W, D_H))
GAMECLOCK = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Font stuff
pygame.font.init()
myfont = pygame.font.SysFont('franklingothicmedium', 20)

FPScounter = False

# Getting tilemap from text file
with open('tilemap.txt', 'r') as f:
    TILEMAP = []
    for line in f:
        if len(line) == 1:  # If line empty / If tilemap has been scanned ; Allows comments in tilemap.txt
            break
        line = line.replace('\n', '')
        line = [int(i) for i in str(line)]  # Turns number to a list of digits
        TILEMAP.append(line)


def raycast(rayangle):
    # Consider manual rayangle correction if it's parallel with any of the gridlines

    ray_x = PLAYER_X
    ray_y = PLAYER_Y

    # Variables depending
    #   on the rayangle
    #          |
    #    A = 0 | A = 0
    #    B = 0 | B = 1
    #   -------|-------
    #    A = 1 | A = 1
    #    B = 0 | B = 1
    #          |

    if rayangle > 0:
        A = 1
    else:
        A = 0
    if abs(rayangle) < pi / 2:
        B = 1
    else:
        B = 0

    hit = False
    while not hit:

        x_offset = ray_x - int(ray_x)
        y_offset = ray_y - int(ray_y)

        # If (x or y)_offset == (A or B) only resets offset depending on the angle
        # Otherwise ray will get stuck on some angles
        if y_offset == A:
            y_offset = 1
        horizontalInterception_x = (A - y_offset) / tan(rayangle)
        horizontalInterception_y = A - y_offset

        if x_offset == B:
            x_offset = 1
        verticalInterception_y = (B - x_offset) * tan(rayangle)
        verticalInterception_x = B - x_offset

        # Getting the distances squared values because sqrt() is slow
        horizontalInterception_dist_squared = horizontalInterception_x ** 2 + horizontalInterception_y ** 2
        verticalInterception_dist_squared = verticalInterception_x ** 2 + verticalInterception_y ** 2

        # If hitting horizontal gridline
        if horizontalInterception_dist_squared < verticalInterception_dist_squared:
            ray_x += horizontalInterception_x
            ray_y += horizontalInterception_y

            # Map positions to check
            map_y = int(ray_y) + (A - 1)
            map_x = int(ray_x)
            grid_value = TILEMAP[map_y][map_x]
            color_multiplier = 1

        # If hitting vertical gridline
        else:
            ray_x += verticalInterception_x
            ray_y += verticalInterception_y

            # Map positions to check
            map_y = int(ray_y)
            map_x = int(ray_x) + (B - 1)
            grid_value = TILEMAP[map_y][map_x]
            color_multiplier = 0.5

        if grid_value != 0:  # If anything other than 0; If hitting a wall/something

            deltax = ray_x - PLAYER_X
            deltay = ray_y - PLAYER_Y

            distance_along_VIEWANGLE = deltax * cos(VIEWANGLE) + deltay * sin(VIEWANGLE)  # Needed to avoid fisheye
            WALL_DATA.append((distance_along_VIEWANGLE, grid_value, color_multiplier))

            hit = True


def draw_walls():
    global WALL_DATA
    constant = 0.8 * D_H
    wall_width = D_W / RAYS

    for i, wall in enumerate(WALL_DATA):
        # Naming the values stored in element
        distance_along_VIEWANGLE = wall[0]
        grid_value = wall[1]
        color_multiplier = wall[2]

        wall_height = constant / distance_along_VIEWANGLE
        if wall_height > D_H:
            wall_height = D_H

        rect_start_pos = (i * wall_width, (D_H - wall_height) / 2)
        rect_size = (wall_width, wall_height)

        # Takes the value stored in COLOURS and multiplies each rgb value by color_multiplier
        rect_color = tuple(color_multiplier*x for x in COLOURS[grid_value])

        pygame.draw.rect(GAMEDISPLAY, rect_color, (rect_start_pos, rect_size))
    WALL_DATA = []


def rays():
    # Sending rays to calculate
    starting_angle = VIEWANGLE - FOV / 2
    rayangles_difference = FOV / RAYS
    for i in range(RAYS):
        rayangle = fixed_angle(starting_angle + i * rayangles_difference)
        raycast(rayangle)


def fixed_angle(angle):
    # Function made for angles to never go over abs(pi)
    # For example 3.18 will be turned to -3.10, bc it's 0.04 over pi

    if angle > pi:  # 3.14+
        over_the_limit = angle - pi
        angle = -pi + over_the_limit

    elif angle < -pi:  # 3.14-
        over_the_limit = angle + pi
        angle = pi + over_the_limit

    return angle


def mouse():
    global VIEWANGLE

    mouse_x_change = pygame.mouse.get_rel()[0]
    VIEWANGLE += mouse_x_change * SENSITIVITY

    # Reseting VIEWANGLE if it gets too big
    VIEWANGLE = fixed_angle(VIEWANGLE)


def movement():
    global PLAYER_X, PLAYER_Y

    keys = pygame.key.get_pressed()

    if keys[K_w] or keys[K_a] or keys[K_s] or keys[K_d]:
        movement_x = 0
        movement_y = 0
        if keys[K_w]:
            movement_x += cos(VIEWANGLE)
            movement_y += sin(VIEWANGLE)

        if keys[K_a]:
            movement_x += cos(fixed_angle(VIEWANGLE - pi / 2))
            movement_y += sin(fixed_angle(VIEWANGLE - pi / 2))

        if keys[K_s]:
            movement_x += cos(fixed_angle(VIEWANGLE - pi))
            movement_y += sin(fixed_angle(VIEWANGLE - pi))

        if keys[K_d]:
            movement_x += cos(fixed_angle(VIEWANGLE + pi / 2))
            movement_y += sin(fixed_angle(VIEWANGLE + pi / 2))

        # Needed for normalize() function
        movement_vector = np.asarray([[movement_x, movement_y]])

        # Normalized vector
        normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
        movement_x = normalized_vector[0] * PLAYER_SPEED
        movement_y = normalized_vector[1] * PLAYER_SPEED

        PLAYER_X += movement_x
        PLAYER_Y += movement_y
        player_collision(movement_x)  # Corrects player position when needed


def player_collision(movement_x):
    # As long as HITBOX_HALFSIZE >= PLAYER_SPEED, collisions should work
    # If not, player could clip inside a wall, making the program reset it's position incorrectly
    # For example when hitbox right side would be colliding with a wall at 13.01,
    # it would reset x to 14 - HITBOX_HALFSIZE instead of 13 - HITBOX_HALFSIZE
    #
    # Function requires movement_x bc in one point interceptions, old_x is needed

    global PLAYER_X, PLAYER_Y

    # Checking if hitbox edges collide with a object/wall
    down_right = TILEMAP[int(PLAYER_Y + HITBOX_HALFSIZE)][int(PLAYER_X + HITBOX_HALFSIZE)] != 0
    up_right = TILEMAP[int(PLAYER_Y - HITBOX_HALFSIZE)][int(PLAYER_X + HITBOX_HALFSIZE)] != 0
    down_left = TILEMAP[int(PLAYER_Y + HITBOX_HALFSIZE)][int(PLAYER_X - HITBOX_HALFSIZE)] != 0
    up_left = TILEMAP[int(PLAYER_Y - HITBOX_HALFSIZE)][int(PLAYER_X - HITBOX_HALFSIZE)] != 0
    edges = (down_right, up_right, down_left, up_left)

    # If touching anything to begin with
    if any(edges):
        x_collision = False
        y_collision = False

        # If diagonals touching
        if down_right and up_left or down_left and up_right:
            x_collision = True
            y_collision = True

        # If top or bottom touching
        elif down_right and down_left or up_right and up_left:
            y_collision = True

        # If left or right touching
        elif down_right and up_right or down_left and up_left:
            x_collision = True

        else:
            # If it reaches here it has to be one point interception
            for c, edge in enumerate(edges):  # Step through all the edges
                if edge:  # If the interception edge found
                    if c < 2:  # If down_right or up_right
                        current_x = PLAYER_X + HITBOX_HALFSIZE

                    else:  # If down_left or up_left
                        current_x = PLAYER_X - HITBOX_HALFSIZE

                    old_x = current_x - movement_x  # This is where movement_x is needed

                    # If x was already reset on previous frame or if it has exited it's grid position
                    if old_x == int(old_x) or int(old_x) != int(current_x):
                        x_collision = True
                    else:
                        y_collision = True

        if x_collision:
            # Hitbox left side colliding
            if PLAYER_X - int(PLAYER_X) < HITBOX_HALFSIZE:
                PLAYER_X = int(PLAYER_X) + HITBOX_HALFSIZE

            # Hitbox right side colliding
            else:
                PLAYER_X = ceil(PLAYER_X) - HITBOX_HALFSIZE

        if y_collision:
            # Hitbox upper side colliding
            if PLAYER_Y - int(PLAYER_Y) < HITBOX_HALFSIZE:
                PLAYER_Y = int(PLAYER_Y) + HITBOX_HALFSIZE
            # Hitbox lower side colliding
            else:
                PLAYER_Y = ceil(PLAYER_Y) - HITBOX_HALFSIZE


def events():
    global running
    global FPScounter

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_F1:
                FPScounter = not FPScounter  # Toggles the counter
            if event.key == K_ESCAPE:
                running = False


def top_layer_sprites():
    if FPScounter == True:
        FPStext = 'FPS: {}'.format(int(GAMECLOCK.get_fps()))
        FPSimage = myfont.render(FPStext, True, (255, 255, 255))
        GAMEDISPLAY.blit(FPSimage, (4, 0))


def game_loop():
    global running  # Making running global so it's accessible in keys() and events()
    running = True
    while running:
        GAMEDISPLAY.fill((0, 0, 0))

        events()

        mouse()
        movement()

        rays()
        draw_walls()
        top_layer_sprites()

        pygame.display.flip()
        GAMECLOCK.tick(60)

    pygame.quit()


game_loop()
