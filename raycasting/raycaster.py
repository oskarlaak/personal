# Main TODOs:
# Interception type (horizontal/vertical) could be determined faster without manually comparing squared distances
# Player collision
# Wall height??

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

D_W = 1920
D_H = 1080
FPS = 30
FOV = 1.4  # 1.4 radians == about 80 degrees
RAYS = 240  # Drawing frequency across the screen ; Rays casted each frame ; D_W / RAYS should always be int
VIEWANGLE = 0.1  # Any starting VIEWANGLE parallel with a gridline will run into errors
SENSITIVITY = 0.003

PLAYER_X = 6.5
PLAYER_Y = 2.3
PLAYER_SPEED = 0.14
HITBOX_HALFSIZE = 0.14  # Player's hitbox halfsize

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

# Getting tilemap from text file
with open('tilemap.txt', 'r') as f:
    TILEMAP = []
    for line in f:
        if len(line) == 1:  # If line empty; If tilemap has been scanned; Allows comments in tilemap.txt
            break
        line = line.replace('\n', '')
        line = [int(i) for i in str(line)]  # Turns number to a list of digits
        TILEMAP.append(line)


def wall_calc(rayangle):
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

            map_y = int(ray_y) + (A - 1)
            map_x = int(ray_x)
            grid_value = TILEMAP[map_y][map_x]
            color_multiplier = 1

        # If hitting vertical gridline
        else:
            ray_x += verticalInterception_x
            ray_y += verticalInterception_y

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


# Sending rays to calculate
def rays():
    starting_angle = VIEWANGLE - FOV / 2
    rayangles_difference = FOV / RAYS
    for i in range(RAYS):
        rayangle = fixed_angle(starting_angle + i * rayangles_difference)
        wall_calc(rayangle)


def fixed_angle(angle):
    # Function made for angles to never go over abs(pi)
    # For example 3.18 will be turned to -3.10, bc it's 0.04 over pi
    if abs(angle) <= pi:  # If already normal
        return angle

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


def keys():
    global running
    global PLAYER_X, PLAYER_Y

    keys = pygame.key.get_pressed()
    if keys[K_ESCAPE]:
        running = False

    # Movement
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
        player_collision()  # Resets x or y if needed


def player_collision():
    # One point collision interceptions not done

    # As long as HITBOX_HALFSIZE >= PLAYER_SPEED, collisions should work
    # When not, player could clip inside a wall, making the program reset it's position incorrectly
    # For example when hitbox right side would be hitting a wall at 13.01,
    # it would reset x to 14 - HITBOX_HALFSIZE instead of 13 - HITBOX_HALFSIZE

    global PLAYER_X, PLAYER_Y

    down_right = TILEMAP[int(PLAYER_Y + HITBOX_HALFSIZE)][int(PLAYER_X + HITBOX_HALFSIZE)]
    down_left = TILEMAP[int(PLAYER_Y + HITBOX_HALFSIZE)][int(PLAYER_X - HITBOX_HALFSIZE)]
    up_right = TILEMAP[int(PLAYER_Y - HITBOX_HALFSIZE)][int(PLAYER_X + HITBOX_HALFSIZE)]
    up_left = TILEMAP[int(PLAYER_Y - HITBOX_HALFSIZE)][int(PLAYER_X - HITBOX_HALFSIZE)]

    x_collision = False
    y_collision = False

    # Requires a bit of thinking to get it around your head, but it's managable
    # Feel like commenting it will make it even harder to read
    # Should be about as optimized as you can get with somewhat realistic collision
    # If there is only one interception point, x and y offsets are needed

    if down_right != 0:
        if down_left != 0:
            y_collision = True
            if up_right != 0 or up_left != 0:
                x_collision = True
        elif up_right != 0:
            x_collision = True
            if up_left != 0:
                y_collision = True
        else:
            pass
            #x_offset = PLAYER_X + HITBOX_HALFSIZE - int(PLAYER_X + HITBOX_HALFSIZE)
            #y_offset = PLAYER_Y + HITBOX_HALFSIZE - int(PLAYER_Y + HITBOX_HALFSIZE)
            #
            ## If changing x makes more sense
            #if x_offset < y_offset:
            #    x_collision = True
            ## If changing y makes more sense
            #else:
            #    y_collision = True

    elif up_left != 0:
        if up_right != 0:
            y_collision = True
            if down_left != 0:
                x_collision = True
        elif down_left != 0:
            x_collision = True

        else:
            pass

    elif up_right != 0:
        pass

    elif down_left != 0:
        pass


    # Applying changes to x and y position
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


def game_loop():

    global running  # Making running global so it's accessible in keys()
    running = True
    while running:
        GAMEDISPLAY.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        mouse()
        keys()

        rays()
        draw_walls()

        pygame.display.flip()
        GAMECLOCK.tick(FPS)

    pygame.quit()


game_loop()
