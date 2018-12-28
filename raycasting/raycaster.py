# Main TODOs:
# Finish tilemap bottom right side which is not completely done
#
# Simple wall texturing (for example black lines on the bottom of the wall)
#
# Perhaps PLAYER could be a class to clean code
#
# Toggleable shades and maybe add draw settings (color_multiplier)

# NOTES:
# Somewhat laggy in big open areas
# Movement keys are handled in movement() and other keys in events()
# Collisions are still not 100% working - needs testing
# All angles are in radians

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

D_W = 1920
D_H = 1080
FOV = 1.4  # 1.4 radians == about 80 degrees
RAYS = 240  # Drawing frequency across the screen / Rays casted each frame ; D_W / RAYS should always be int
VIEWANGLE = 0
SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved

PLAYER_X = 30.5
PLAYER_Y = 58.5
PLAYER_SPEED = 0.1  # Must be <= HITBOX_HALFSIZE - not a problem with high tickrates
HITBOX_HALFSIZE = 0.2  # Player's hitbox halfsize

WALL_DATA = []

# Naming colours
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Assigning colours to tilemap indexes
TILEMAP_COLOURS = {
    1: RED,
    2: GREEN,
    3: BLUE
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

info_layer = False

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
    #   Variables depending
    #     on the rayangle
    #            |
    #      A = 0 | A = 1
    # -pi  B = 0 | B = 0  -
    #     -------|------- 0 rad
    #  pi  A = 0 | A = 1  +
    #      B = 1 | B = 1
    #            |

    if abs(rayangle) > pi / 2:
        A = 0
    else:
        A = 1
    if rayangle < 0:
        B = 0
    else:
        B = 1

    ray_x = PLAYER_X
    ray_y = PLAYER_Y

    while True:
        # "if (x/y)_offset == (A/B)" only resets offset depending on the rayangle
        # This will help to determine interception type correctly
        # and it also prevents rays getting stuck on some angles

        x_offset = ray_x - int(ray_x)
        if x_offset == A:
            x_offset = 1

        y_offset = ray_y - int(ray_y)
        if y_offset == B:
            y_offset = 1

        # Very simple system
        # Every loop it blindly calculates vertical* gridline Interception_y and checks it's distance
        # to determine the interception type and to calculate other varibles depending on that interception type
        # Originally it remembered previous interception type to calculate the new one
        # but doing it this way turns out to be slightly faster
        #
        # *It calculates vertical gridline interception by default bc in those calculations
        # there are no divisions which could bring up ZeroDivisionError

        Interception_y = (A - x_offset) * tan(rayangle)
        if int(ray_y - y_offset) == int(ray_y + Interception_y):
            # Hitting vertical gridline
            Interception_x = A - x_offset

            ray_x += Interception_x
            ray_y += Interception_y
            map_y = int(ray_y)
            map_x = int(ray_x) + (A - 1)
            side = 0

        else:
            # Hitting horizontal gridline
            Interception_x = (B - y_offset) / tan(rayangle)
            Interception_y = B - y_offset

            ray_x += Interception_x
            ray_y += Interception_y
            map_y = int(ray_y) + (B - 1)
            map_x = int(ray_x)
            side = 1

        grid_value = TILEMAP[map_y][map_x]

        if grid_value != 0:  # If anything other than 0 ; If hitting a wall/something
            deltax = ray_x - PLAYER_X
            deltay = ray_y - PLAYER_Y

            # Perpendicular distance needed to avoid fisheye
            perpendicular_distance = deltax * cos(VIEWANGLE) + deltay * sin(VIEWANGLE)

            WALL_DATA.append((perpendicular_distance, grid_value, side))

            break


def draw_walls():
    global WALL_DATA

    constant = 0.8 * D_H
    wall_width = D_W / RAYS

    for i, wall in enumerate(WALL_DATA):
        # Naming the values stored in element
        p = wall[0]
        grid_value = wall[1]
        side = wall[2]

        color_multiplier = 1 - side / 2

        wall_height = constant / p
        if wall_height > D_H:
            wall_height = D_H

        rect_start_pos = (i * wall_width, (D_H - wall_height) / 2)
        rect_size = (wall_width, wall_height)

        # Takes the value stored in TILEMAP_COLOURS and multiplies each rgb value by color_multiplier
        rect_color = tuple(color_multiplier*x for x in TILEMAP_COLOURS[grid_value])

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
        angle -= 2 * pi

    elif angle < -pi:  # 3.14-
        angle += 2 * pi

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
    global info_layer

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_F1:
                info_layer = not info_layer  # Toggles the counter
            if event.key == K_ESCAPE:
                running = False


def top_layer_sprites():
    if info_layer:
        decimals = 3
        FPStext = 'FPS: {}'.format(int(GAMECLOCK.get_fps()))
        FPSimage = myfont.render(FPStext, True, WHITE)

        PLAYER_Xtext = 'X: {}'.format(round(PLAYER_X, decimals))
        PLAYER_Ximage = myfont.render(PLAYER_Xtext, True, WHITE)

        PLAYER_Ytext = 'Y: {}'.format(round(PLAYER_Y, decimals))
        PLAYER_Yimage = myfont.render(PLAYER_Ytext, True, WHITE)

        VIEWANGLEtext = 'RAD: {}'.format(round(VIEWANGLE, decimals))
        VIEWANGLEimage = myfont.render(VIEWANGLEtext, True, WHITE)

        GAMEDISPLAY.blit(FPSimage, (4, 0))
        GAMEDISPLAY.blit(PLAYER_Ximage, (4, 20))
        GAMEDISPLAY.blit(PLAYER_Yimage, (4, 40))
        GAMEDISPLAY.blit(VIEWANGLEimage, (4, 60))


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
