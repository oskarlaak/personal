# Main TODOs:
# Wall rendering can be more optimized so it doesn't calculate two interceptions every move
# Depending on the interception type, some walls could be made darker
# Player collision

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

D_W = 1920
D_H = 1080
FPS = 30
FOV = 1.4  # 1.4 radians == about 80 degrees
RAYS = 240  # Drawing frequency across the screen, D_W / RAYS should always be int
VIEWANGLE = 0.1  # Any starting VIEWANGLE parallel with a gridline will run into errors
SENSITIVITY = 0.003

PLAYER_X = 6.5
PLAYER_Y = 2.3
PLAYER_SPEED = 0.14
HITBOX_HALFSIZE = 0.1  # Player's hitbox halfsize

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

        # If hitting vertical gridline
        else:
            ray_x += verticalInterception_x
            ray_y += verticalInterception_y

        grid_value = check_interception(ray_x, ray_y)
        if grid_value != 0:  # If anything other than 0; If hitting a wall/something

            deltax = ray_x - PLAYER_X
            deltay = ray_y - PLAYER_Y

            distance_along_VIEWANGLE = deltax * cos(VIEWANGLE) + deltay * sin(VIEWANGLE)  # Needed to avoid fisheye
            WALL_DATA.append((distance_along_VIEWANGLE, grid_value))

            hit = True


def draw_walls():
    global WALL_DATA
    constant = 0.8 * D_H
    wall_width = D_W / RAYS

    for i, wall in enumerate(WALL_DATA):
        distance_along_VIEWANGLE = wall[0]
        grid_value = wall[1]

        wall_height = constant / distance_along_VIEWANGLE
        if wall_height > D_H:
            wall_height = D_H

        rect_start_pos = (i * wall_width, (D_H - wall_height) / 2)
        rect_size = (wall_width, wall_height)
        pygame.draw.rect(GAMEDISPLAY, COLOURS[grid_value], (rect_start_pos, rect_size))
    WALL_DATA = []


# Sending rays to calculate
def rays():
    starting_angle = VIEWANGLE - FOV / 2
    rayangles_difference = FOV / RAYS
    for i in range(RAYS):
        rayangle = fixed_angle(starting_angle + i * rayangles_difference)
        wall_calc(rayangle)


def fixed_angle(angle):
    # Fuction made for angles to never go over abs(pi)
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


def check_interception(x, y):
    # Checking both sides of the intercepted gridline and returning the grid_value

    if x == int(x):  # If touching vertical gridline
        if TILEMAP[int(y)][int(x)] != 0:  # Checking right side of the vertical gridline
            return TILEMAP[int(y)][int(x)]

        if TILEMAP[int(y)][int(x) - 1] != 0:  # Checking left side of the vertical gridline
            return TILEMAP[int(y)][int(x) - 1]

    elif y == int(y):  # If touching horizontal gridline
        if TILEMAP[int(y)][int(x)] != 0:  # Checking lower side of the horizontal gridline
            return TILEMAP[int(y)][int(x)]

        if TILEMAP[int(y) - 1][int(x)] != 0:  # Checking upper side of the horizontal gridline
            return TILEMAP[int(y) - 1][int(x)]

    return 0


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

        # Needed for normalize() funtion
        movement_vector = np.asarray([[movement_x, movement_y]])

        # Normalized vector
        normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
        movement_x = normalized_vector[0]
        movement_y = normalized_vector[1]

        PLAYER_X += movement_x * PLAYER_SPEED
        PLAYER_Y += movement_y * PLAYER_SPEED

        # Collision to be made


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
