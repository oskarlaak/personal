# Main TODOs:
# Doors
# Enemies/other sprites when dissortion fixed
# Rename variables so they are all in camelCase
# Try putting texture loading into try/except to get rid of yellow boxes around load

# IMPORTANT
# Rayangles need to be equally spaced in camera plane rather than equally different by radians -
# this is what is making aa slight dissortion especially on higher FOVs

# NOTES:
# Tilemap only supports 9 different wall types bc tilemap indexes are from 0 to 9
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

D_W = 1280
D_H = 720

# Pygame stuff
pygame.init()
pygame.display.set_caption('Raycaster')
DISPLAY = pygame.display.set_mode((D_W, D_H))
CLOCK = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

FOV = pi / 2  # = 90 degrees
RAYS = int(D_W / 6)  # Drawing frequency across the screen / Rays casted each frame ; D_W / RAYS must always be int
SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved

WALL_DATA = []

TEXTURE_SIZE = 64
stone_wall_01 = pygame.image.load('textures/stone_wall_01_light.png').convert_alpha()
stone_wall_01_dark = pygame.image.load('textures/stone_wall_01_dark.png').convert_alpha()

stone_wall_01_naziflag = pygame.image.load('textures/stone_wall_01_naziflag_light.png').convert_alpha()
stone_wall_01_naziflag_dark = pygame.image.load('textures/stone_wall_01_naziflag_dark.png').convert_alpha()

# Assigning textures to tilemap indexes
TILEMAP_TEXTURES = {
    1: (stone_wall_01, stone_wall_01_dark),
    2: (stone_wall_01_naziflag, stone_wall_01_naziflag_dark),
    3: None
}

# Font stuff
pygame.font.init()
myfont = pygame.font.SysFont('franklingothicmedium', 20)

# Game settings
info_layer = False
fullscreen = False

# Getting tilemap from text file
with open('tilemap.txt', 'r') as f:
    TILEMAP = []
    for line in f:
        if len(line) == 1:  # If line only consists of '\n' / If line empty ; Allows comments in tilemap.txt
            break
        line = line.replace('\n', '')
        line = [int(i) for i in str(line)]  # Turns number to a list of digits
        TILEMAP.append(line)


class Player:
    speed = 0.1  # Must be <= halfHitbox

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.viewangle = angle

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def move(self, x, y):
        self.x += x
        self.y += y

        # Hitbox sides
        halfHitbox = 0.2
        right = self.x + halfHitbox
        left = self.x - halfHitbox
        down = self.y + halfHitbox
        up = self.y - halfHitbox

        down_right = TILEMAP[int(down)][int(right)] != 0
        down_left = TILEMAP[int(down)][int(left)] != 0
        up_right = TILEMAP[int(up)][int(right)] != 0
        up_left = TILEMAP[int(up)][int(left)] != 0

        # If hitting something, find the collision type
        if down_right or up_right or down_left or up_left:
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
            # If one corner touching
            else:
                if down_right:
                    edge_x = right
                    edge_y = down
                elif down_left:
                    edge_x = left
                    edge_y = down
                elif up_right:
                    edge_x = right
                    edge_y = up
                else:
                    edge_x = left
                    edge_y = up

                x_offset = edge_x - int(edge_x)
                y_offset = edge_y - int(edge_y)

                # Distance to closest round(x/y)
                deltax = abs(round(x_offset) - x_offset)
                deltay = abs(round(y_offset) - y_offset)
                if deltax < deltay:
                    x_collision = True
                else:
                    y_collision = True

            if x_collision:
                if self.x - int(self.x) < halfHitbox:
                    self.x = int(self.x) + halfHitbox
                else:
                    self.x = ceil(self.x) - halfHitbox

            if y_collision:
                if self.y - int(self.y) < halfHitbox:
                    self.y = int(self.y) + halfHitbox
                else:
                    self.y = ceil(self.y) - halfHitbox


PLAYER = Player(29.5, 57.5, 0)


def raycast():
    # Precalculating PLAYER's viewangle Dir(X/Y) to use it when collision found
    viewangleDirX = cos(PLAYER.viewangle)
    viewangleDirY = sin(PLAYER.viewangle)

    # Sending rays to later draw walls
    starting_angle = PLAYER.viewangle - FOV / 2
    radians_step = FOV / RAYS  # The amount of radians one rayangle is different from another

    for ray in range(RAYS):
        rayangle = fixed_angle(starting_angle + ray * radians_step)
        tan_rayangle = tan(rayangle)

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

        ray_x = PLAYER.x
        ray_y = PLAYER.y

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

            interception_y = (A - x_offset) * tan_rayangle
            if int(ray_y - y_offset) == int(ray_y + interception_y):
                # Hitting vertical gridline
                interception_x = A - x_offset

                ray_x += interception_x
                ray_y += interception_y
                map_y = int(ray_y)
                map_x = int(ray_x) + (A - 1)
                side = 1

            else:
                # Hitting horizontal gridline
                interception_x = (B - y_offset) / tan_rayangle
                interception_y = B - y_offset

                ray_x += interception_x
                ray_y += interception_y
                map_y = int(ray_y) + (B - 1)
                map_x = int(ray_x)
                side = 0

            grid_value = TILEMAP[map_y][map_x]

            if grid_value != 0:  # If anything other than 0 ; If hitting a wall/something
                deltax = ray_x - PLAYER.x
                deltay = ray_y - PLAYER.y

                # Perpendicular distance needed to avoid fisheye
                perpendicular_distance = deltax * viewangleDirX + deltay * viewangleDirY

                wall_texture = TILEMAP_TEXTURES[grid_value][side]
                if side == 0:
                    offset = ray_x - int(ray_x)
                else:
                    offset = ray_y - int(ray_y)

                # Column that the draw_walls() is going to take from the texture
                column = int(TEXTURE_SIZE * offset)

                WALL_DATA.append((perpendicular_distance, wall_texture, column))

                break


def draw_walls():
    global WALL_DATA

    constant = 1.0 * D_H
    wall_width = int(D_W / RAYS)

    for i, wall in enumerate(WALL_DATA):
        # Naming the values stored in element
        p = wall[0]
        texture = wall[1]
        column = wall[2]
        wall_height = int(constant / p)

        # Getting the part of texture that's going to be scaled and blitted
        image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)

        # For optimization, walls that are bigger than D_H are going to be cropped
        # Without it, framerates drop drastically when staring into a wall
        if wall_height > D_H:
            # Complicated system that will crop the image and then adjust wall_height accordingly
            # Cropping before scaling bc it removes the need to scale to enormous sizes

            # Percentage of image that's going to be seen
            percentage = D_H / wall_height

            # What would be the perfect cropping size
            perfect_size = TEXTURE_SIZE * percentage

            # Actual (cropping) size needs to be the closest even number rounding up perfect_size
            # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
            actual_size = ceil(perfect_size)
            if actual_size % 2 != 0:  # If odd
                actual_size += 1  # Make it even

            image = image.subsurface(0, (TEXTURE_SIZE - actual_size) / 2, 1, actual_size)

            # Adjusting wall_height so it later blits it in the right position
            multiplier = actual_size / perfect_size
            wall_height = int(D_H * multiplier)

        image = pygame.transform.scale(image, (wall_width, wall_height))
        image_pos = (i * wall_width, (D_H - wall_height) / 2)

        DISPLAY.blit(image, image_pos)

    WALL_DATA = []


def fixed_angle(angle):
    # Function made for angles to never go over +-pi
    # For example 3.18 will be turned to -3.10, bc it's 0.04 over pi

    if angle > pi:  # 3.14+
        angle -= 2 * pi

    elif angle < -pi:  # 3.14-
        angle += 2 * pi

    return angle


def mouse():
    radians = pygame.mouse.get_rel()[0] * SENSITIVITY
    PLAYER.rotate(radians)


def movement():
    keys = pygame.key.get_pressed()

    if keys[K_w] or keys[K_a] or keys[K_s] or keys[K_d]:
        movement_x = 0
        movement_y = 0
        if keys[K_w]:
            movement_x += cos(PLAYER.viewangle)
            movement_y += sin(PLAYER.viewangle)

        if keys[K_a]:
            movement_x += cos(PLAYER.viewangle - pi / 2)
            movement_y += sin(PLAYER.viewangle - pi / 2)

        if keys[K_s]:
            movement_x += cos(PLAYER.viewangle - pi)
            movement_y += sin(PLAYER.viewangle - pi)

        if keys[K_d]:
            movement_x += cos(PLAYER.viewangle + pi / 2)
            movement_y += sin(PLAYER.viewangle + pi / 2)

        # Needed for normalize() function
        movement_vector = np.asarray([[movement_x, movement_y]])

        # Normalized vector
        normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
        movement_x = normalized_vector[0] * PLAYER.speed
        movement_y = normalized_vector[1] * PLAYER.speed

        PLAYER.move(movement_x, movement_y)


def events():
    global running
    global info_layer
    global fullscreen

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            if event.key == K_F1:
                info_layer = not info_layer
            if event.key == K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    pygame.display.set_mode((D_W, D_H), pygame.FULLSCREEN)
                else:
                    pygame.display.set_mode((D_W, D_H))


def bottom_layer():
    pygame.draw.rect(DISPLAY, ( 50,  50,  50), ((0,       0), (D_W, D_H / 2)))  # Ceiling
    pygame.draw.rect(DISPLAY, (100, 100, 100), ((0, D_H / 2), (D_W, D_H / 2)))  # Floor


def top_layer():
    if info_layer:
        text_color = (255, 255, 255)
        decimals = 3

        FPStext = 'FPS: {}'.format(int(CLOCK.get_fps()))
        FPSimage = myfont.render(FPStext, True, text_color)

        PLAYER_Xtext = 'X: {}'.format(round(PLAYER.x, decimals))
        PLAYER_Ximage = myfont.render(PLAYER_Xtext, True, text_color)

        PLAYER_Ytext = 'Y: {}'.format(round(PLAYER.x, decimals))
        PLAYER_Yimage = myfont.render(PLAYER_Ytext, True, text_color)

        VIEWANGLEtext = 'RAD: {}'.format(round(PLAYER.viewangle, decimals))
        VIEWANGLEimage = myfont.render(VIEWANGLEtext, True, text_color)

        DISPLAY.blit(FPSimage, (4, 0))
        DISPLAY.blit(PLAYER_Ximage, (4, 20))
        DISPLAY.blit(PLAYER_Yimage, (4, 40))
        DISPLAY.blit(VIEWANGLEimage, (4, 60))


def game_loop():
    global running  # Making running global so it's accessible in events()
    running = True
    while running:
        bottom_layer()

        events()

        mouse()
        movement()

        raycast()
        draw_walls()
        top_layer()

        pygame.display.flip()
        CLOCK.tick(60)

    pygame.quit()

game_loop()
