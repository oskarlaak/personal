# TO DO:
# Player shot detection
# Enemy getting hit/dying
# Enemy attack

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians
# Objects are in OBJECTS list only if that object's cell is visible to player
# Enemies are in ENEMIES list at all times bc moving objects are harder to optimize
# Wall texture files require two textures side by side (even if they are going to be the same),
# bc raycast() is going to pick one based on the side of the interception
# All timed events are tick based,
# meaning that changing fps will change timer time


class Player:
    speed = 0.15  # Must be < half_hitbox, otherwise collisions will not work
    half_hitbox = 0.2

    def __init__(self, pos, angle):
        self.x, self.y = pos
        self.viewangle = angle + 0.0000001
        self.hp = 100
        self.ammo = 60

        self.weapon_nr = 1

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def shoot(self, weapon):
        # When player sends out a bullet
        weapon.mag_ammo -= 1

    def reload(self, weapon):
        ammo_needed = weapon.mag_size - weapon.mag_ammo

        if not weapon.ammo_unlimited:
            if ammo_needed > self.ammo:
                ammo_needed = self.ammo
            self.ammo -= ammo_needed

        weapon.mag_ammo += ammo_needed

    def move(self, x_move, y_move):

        def one_point_collision(y, x):
            if int(x - x_move) == x - x_move:
                return True, False
            if int(y - y_move) == y - y_move:
                return False, True

            x_offset = x - int(x)
            y_offset = y - int(y)

            # Distance to closest round(x/y)
            deltax = abs(round(x_offset) - x_offset)
            deltay = abs(round(y_offset) - y_offset)
            if deltax < deltay:
                return True, False
            else:
                return False, True

        # Start off by moving player position
        self.x += x_move
        self.y += y_move

        # Hitbox sides
        right = self.x + Player.half_hitbox
        left = self.x - Player.half_hitbox
        down = self.y + Player.half_hitbox
        up = self.y - Player.half_hitbox

        # Hitbox corners
        # Everything that player can walk on is less than 0 on tilemap
        # So these will be True if there is a collision
        down_right = TILEMAP[int(down)][int(right)] > 0
        down_left = TILEMAP[int(down)][int(left)] > 0
        up_right = TILEMAP[int(up)][int(right)] > 0
        up_left = TILEMAP[int(up)][int(left)] > 0

        # Find the collision type
        x_collision = False
        y_collision = False

        if down_right:
            if up_left:
                x_collision = True
                y_collision = True
            elif down_left:
                y_collision = True
                if up_right:
                    x_collision = True
            elif up_right:
                x_collision = True
            else:
                x_collision, y_collision = one_point_collision(down, right)

        elif up_left:
            if down_left:
                x_collision = True
                if up_right:
                    y_collision = True
            elif up_right:
                y_collision = True
            else:
                x_collision, y_collision = one_point_collision(up, left)

        elif down_left:
            x_collision, y_collision = one_point_collision(down, left)

        elif up_right:
            x_collision, y_collision = one_point_collision(up, right)

        # Apply changes to x/y if there was a collision
        if x_collision:
            if self.x - int(self.x) < Player.half_hitbox:
                self.x = int(self.x) + Player.half_hitbox
            else:
                self.x = ceil(self.x) - Player.half_hitbox

        if y_collision:
            if self.y - int(self.y) < Player.half_hitbox:
                self.y = int(self.y) + Player.half_hitbox
            else:
                self.y = ceil(self.y) - Player.half_hitbox


class WeaponModel:
    switch_ticks = 20

    def __init__(self):
        self.shooting = False
        self.ticks = 0  # A var to store time
        self.column = 0
        self.reloading = False
        self.switching = 0

        self.draw_y = 0

    def shoot(self, weapon):
        # Shooting animation system
        self.ticks += 1
        if self.ticks == weapon.fire_delay / weapon.animation_frames:
            self.ticks = 0

            self.column += 1

            if self.column > weapon.animation_frames:  # If finished shot animation
                # If weapon automatic, has magazine ammo and mouse down
                if weapon.automatic and weapon.mag_ammo and pygame.mouse.get_pressed()[0]:
                    self.column = 1  # Keep going
                else:
                    self.column = 0  # End animation
                    self.shooting = False

            if self.column == 1:
                PLAYER.shoot(weapon)

    def reload(self, weapon):
        self.ticks += 1
        if self.ticks <= weapon.reload_time / 2:
            self.draw_y += 20
        elif self.ticks <= weapon.reload_time:
            self.draw_y -= 20
        else:
            self.ticks = 0
            self.reloading = False
            PLAYER.reload(weapon)

    def switch_weapons(self):
        self.ticks += 1
        if self.ticks == WeaponModel.switch_ticks / 2:
            PLAYER.weapon_nr += self.switching  # Switches weapon model when halfway through

        if self.ticks <= WeaponModel.switch_ticks / 2:
            self.draw_y += 40
        elif self.ticks <= WeaponModel.switch_ticks:
            self.draw_y -= 40
        else:
            self.ticks = 0
            self.switching = 0

    def update(self):
        self.weapon = WEAPONS[PLAYER.weapon_nr]

        if self.shooting:
            self.shoot(self.weapon)

        elif self.reloading:
            self.reload(self.weapon)

        elif self.switching:
            self.switch_weapons()

    def draw(self, surface):
        cell_w = self.weapon.weapon_sheet.get_width() / (self.weapon.animation_frames + 1)
        cell_h = self.weapon.weapon_sheet.get_height()
        image = self.weapon.weapon_sheet.subsurface(cell_w * WEAPON_MODEL.column, 0, cell_w, cell_h)
        DISPLAY.blit(image, (D_W / 2, D_H - cell_h + self.draw_y))


class Door:
    speed = 0.04
    open_ticks = 60

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value
        self.ticks = 0
        self.state = 0
        self.opened_state = 0  # 1 is fully opened, 0 is fully closed

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def move(self):
        if self.state > 0:
            if self.state == 1:  # Opening
                self.opened_state += Door.speed
                if self.opened_state > 1:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.opened_state = 1
                    self.state += 1

            if self.state == 2:  # Staying open
                self.ticks += 1
                if self.ticks >= Door.open_ticks:  # If time for door to close
                    # Checking if player is not in door's way
                    safe_dist = 0.5 + Player.half_hitbox
                    if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            if self.state == 3:  # Closing
                self.opened_state -= Door.speed
                if self.opened_state < 0:
                    self.opened_state = 0
                    self.state = 0


class Drawable:
    def adjust_image_height(self):
        # Depending on self.height, (it being the unoptimized image drawing height) this system will crop out
        # from given unscaled image as many pixel rows from top and bottom as possible,
        # while ensuring that the player will not notice a difference, when the image is drawn later
        # (that means it will not crop out pixel rows, that are going to be on the screen)
        #
        # It will then also adjust drawing height, so the program later knows, how big to scale the new cropped image
        #
        # Cropping is done before scaling to ensure that the program is not going to be scaling images to enormous sizes

        # Percentage of image that's going to be seen
        percentage = D_H / self.height

        # What would be the perfect cropping size
        perfect_size = TEXTURE_SIZE * percentage

        # However actual cropping size needs to be the closest even* number rounding up perfect_size
        # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
        # *number needs to be even bc you can't crop at halfpixel
        cropping_size = ceil(perfect_size / 2) * 2

        # Cropping the image smaller - width stays the same
        rect = pygame.Rect((0, (TEXTURE_SIZE - cropping_size) / 2), (self.image.get_width(), cropping_size))
        self.image = self.image.subsurface(rect)

        # Adjusting height accordingly
        multiplier = cropping_size / perfect_size
        self.height = int(D_H * multiplier)  # Rounding it doesn't make difference


class Wall(Drawable):
    def __init__(self, perp_dist, texture, column, count):
        self.perp_dist = perp_dist  # Needs saving to sort by it later

        # Cropping 1 pixel wide column out of texture
        self.image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)

        self.height = int(Drawable.constant / self.perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        # Resizing the image and getting it's position
        self.display_x = count * Wall.width
        self.display_y = (D_H - self.height) / 2
        self.image = pygame.transform.scale(self.image, (Wall.width, self.height))

    def draw(self, surface):
        surface.blit(self.image, (self.display_x, self.display_y))


class Sprite:
    def draw(self, surface):
        # Optimized sprite drawing function made for Enemies and Objects

        if self.perp_dist > 0:
            # Since sprite's out of bounds top and bottom parts are already cut out
            # the program can now draw all sprite pixel columns, that are in display area

            column_width = self.width / TEXTURE_SIZE
            column_left_side = self.display_x
            column_right_side = self.display_x + column_width

            for column in range(TEXTURE_SIZE):
                column_left_side += column_width
                column_right_side += column_width

                if column_left_side < D_W and column_right_side > 0:  # If row on screen

                    # Getting sprite column out of image
                    sprite_column = self.image.subsurface(column, 0, 1, self.image.get_height())

                    # Scaling that column
                    sprite_column = pygame.transform.scale(sprite_column, (ceil(column_width), self.height))

                    # Blitting that column
                    surface.blit(sprite_column, (column_left_side, self.display_y))

    def calc_display_xy(self, angle_from_player):
        # In order to calculate sprite's correct display x/y position, we need to calculate it's camera plane position
        # NOTE: atan2(delta_y, delta_x) is the angle from player to sprite

        camera_plane_pos = CAMERA_PLANE_LEN / 2 + tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE_DIST

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H - self.height) / 2


class Object(Drawable, Sprite):
    def __init__(self, map_pos, tilevalue):
        self.x = map_pos[0] + 0.5
        self.y = map_pos[1] + 0.5

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        if self.perp_dist > 0:
            self.image = TILE_VALUES_INFO[tilevalue][1]  # Name needs to be self.image for it to work in adjust_image_height()

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            angle_from_player = atan2(delta_y, delta_x)

            self.calc_display_xy(angle_from_player)

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)


class Enemy(Drawable, Sprite):

    # Amount of ticks that every image of animation is going to be shown
    # The delay of which images are going to change
    animation_ticks = 5

    # Stationary enemy turning speed
    # Radians per tick as always
    turning_speed = 0.08

    def __init__(self, spritesheet, pos):
        self.x, self.y = self.home = pos
        self.angle = 0  # Enemy actual angle
        self.wanted_angle = 0  # Angle to which enemy is turning
        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.path = []  # Enemy running path

        # Take attributes from ENEMY_INFO based on spritesheet (enemy type)
        # What each attribute means see tilevaluesinfo.py enemy info dictionary description
        self.hp, self.speed, self.memory, self.patience = ENEMY_INFO[self.sheet]

        # Timed events tick (frames passed) variables
        self.anim_ticks = 0  # Time passed during animation
        self.last_saw_ticks = self.memory  # Time passed when the enemy last saw the player
        self.stationary_ticks = 0  # Time enemy has stayed stationary/without moving (turning counts as moving)

        # Creates a list of angles that are going to be chosen by random every once in a while
        # Angles which enemy can see more are chosen more often
        self.look_angles = []
        # 20 different viewangles should be enough
        rayangles = [pi,  pi*.9,  pi*.8,  pi*.7,  pi*.6,  pi*.5,  pi*.4,  pi*.3,  pi*.2,  pi*.1,
                      0, -pi*.9, -pi*.8, -pi*.7, -pi*.6, -pi*.5, -pi*.4, -pi*.3, -pi*.2, -pi*.1]
        for rayangle in rayangles:

            ray_x, ray_y = raycast(rayangle, (self.x, self.y))[1:3]  # <-- Only selects ray_x/ray_y
            ray_dist = sqrt((ray_x - self.x)**2 + (ray_y - self.y)**2)

            for _ in range(int(ray_dist)):
                self.look_angles.append(rayangle)

    def can_see_player(self, player_dist_x, player_dist_y):
        # Returns True if player visible, False if not visible

        # If player in enemy's theoretical 90 degree FOV
        angle_to_player = atan2(-player_dist_y, -player_dist_x)
        if abs(angle_to_player - self.angle) < pi / 4:
            # Check if there is something between enemy and player
            ray_x, ray_y = raycast(angle_to_player, (self.x, self.y))[1:3]  # <-- Only selects ray_x/ray_y
            ray_dist_squared = (self.x - ray_x)**2 + (self.y - ray_y)**2
            player_dist_squared = (player_dist_x)**2 + (player_dist_y)**2
            if ray_dist_squared > player_dist_squared:  # If interception farther than player
                return True
        return False

    def update(self):

        # Enemy door opening system
        # If door underneath enemy,
        # create a door obj in that location if it isn't there already
        # and start opening it immediately
        tile_value = TILEMAP[int(self.y)][int(self.x)]
        tile_id = TILE_VALUES_INFO[tile_value][0]
        if tile_id == ('Door', 'Dynamic'):
            for d in DOORS:
                if (d.x, d.y) == (int(self.x), int(self.y)):
                    d.state = 1
                    break
            else:
                d = Door((int(self.x), int(self.y)), tile_value)
                d.state = 1
                DOORS.append(d)

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        can_see_player = self.can_see_player(delta_x, delta_y)

        # Update last_saw_ticks
        if can_see_player:
            self.last_saw_ticks = 0
        elif self.last_saw_ticks < self.memory:  # Prevents variable getting unnecessarily big
            self.last_saw_ticks += 1

        if not self.path:
            self.stationary_ticks += 1
            if can_see_player:
                self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))

            elif (self.x, self.y) != self.home:  # If enemy without path outside home
                if self.stationary_ticks > self.patience:
                    self.path = pathfinding.pathfind((self.x, self.y), self.home)
            else:
                if self.stationary_ticks > self.patience:  # If been stationary for a while
                    self.wanted_angle = random.choice(self.look_angles)  # Update wanted looking angle

                # Enemy turning system
                if self.angle != self.wanted_angle:
                    self.stationary_ticks = 0  # If turning - not stationary
                    if self.angle < self.wanted_angle:
                        self.angle += Enemy.turning_speed
                    else:
                        self.angle -= Enemy.turning_speed

                    # If self.angle close enough
                    if abs(self.angle - self.wanted_angle) < Enemy.turning_speed:
                        self.angle = self.wanted_angle  # Finish turning

        if self.path:
            self.stationary_ticks = 0

            step_x, step_y = self.path[0]
            step_x += 0.5  # Centers tile pos
            step_y += 0.5

            self.angle = atan2(step_y - self.y, step_x - self.x)
            self.x += cos(self.angle) * self.speed
            self.y += sin(self.angle) * self.speed

            # Could recalculate delta_x/delta_y here but it makes next to no difference

            # If enemy close enough to the path step
            if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                self.x = step_x
                self.y = step_y
                if can_see_player or self.last_saw_ticks < self.memory:
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
                else:
                    del self.path[0]

        angle_from_player = atan2(delta_y, delta_x)
        # Find the right column if enemy running or standing
        # Else it's going to pick it manually - shooting, death animation etc.
        if self.row <= 4:
            angle = fixed_angle(-angle_from_player + self.angle) + pi  # +pi to get rid of negative values
            column = round(angle / (pi / 4))
            if column == 8:
                column = 0

        # Find the right spritesheet row
        if self.path:  # If movement
            if self.row == 0:
                self.row = 1
            # Cycle through running animation
            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks:
                self.anim_ticks = 0
                self.row += 1
                if self.row == 5:
                    self.row = 1
        else:  # If not movement
            self.anim_ticks = 0
            self.row = 0

        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:  # If enemy is going to be drawn, update image for drawing
            self.image = self.sheet.subsurface(column * TEXTURE_SIZE, self.row * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            self.calc_display_xy(angle_from_player)


class Crosshair:
    def __init__(self, width, gap, len, colour):
        self.width = width
        self.gap = gap
        self.len = len
        self.colour = colour

    def draw(self, surface):
        h_w = D_W / 2  # Half width
        h_h = D_H / 2  # Half height
        pygame.draw.line(surface, self.colour, (h_w + self.gap, h_h), (h_w + self.gap + self.len, h_h), self.width)
        pygame.draw.line(surface, self.colour, (h_w - self.gap, h_h), (h_w - self.gap - self.len, h_h), self.width)
        pygame.draw.line(surface, self.colour, (h_w, h_h + self.gap), (h_w, h_h + self.gap + self.len), self.width)
        pygame.draw.line(surface, self.colour, (h_w, h_h - self.gap), (h_w, h_h - self.gap - self.len), self.width)


class Weapon:
    def __init__(self, name, weapon_sheet, animation_frames, fire_delay, mag_size, reload_time, automatic, ammo_unlimited, silenced):
        self.name = name
        self.weapon_sheet = weapon_sheet
        self.animation_frames = animation_frames  # Amount of shot animation frames in weapon_sheet

        self.fire_delay = fire_delay  # Has to be dividable by animation frames
        self.mag_size = mag_size  # Mag's total capacity
        self.mag_ammo = self.mag_size  # Currently ammo in weapon's mag
        self.reload_time = reload_time  # Reloading time in ticks, has to be even number
        self.automatic = automatic
        self.ammo_unlimited = ammo_unlimited
        self.silenced = silenced


def load_weapons():
    # Weapon cells are all 48x32
    ak47 = pygame.image.load('../textures/weapons/ak47.png')
    ak47 = pygame.transform.scale(ak47, (ak47.get_width() * 10, ak47.get_height() * 10)).convert_alpha()
    usps = pygame.image.load('../textures/weapons/usp-s.png')
    usps = pygame.transform.scale(usps, (usps.get_width() * 10, usps.get_height() * 10)).convert_alpha()

    weapons = [None]  # Makes it so first weapon is index 1 insted of 0
    weapons.append(Weapon('AK-47', ak47, 3, 3, 30, 72, True, False, False))
    weapons.append(Weapon('USP-S', usps, 2, 4, 12, 64, False, True, True))
    return weapons


def events():
    global RUNNING

    weapon = WEAPON_MODEL.weapon

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                RUNNING = False

            if event.key == K_r:
                # If magazine not full and weapon not shooting
                if weapon.mag_ammo < weapon.mag_size and not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
                    if weapon.ammo_unlimited:
                        WEAPON_MODEL.reloading = True
                    elif PLAYER.ammo:
                        WEAPON_MODEL.reloading = True

            if event.key == K_e:
                x = int(PLAYER.x + PLAYER.dir_x)
                y = int(PLAYER.y + PLAYER.dir_y)
                tile_id = TILE_VALUES_INFO[TILEMAP[y][x]][0]
                if tile_id[0] == 'Door' and tile_id[1] == 'Dynamic':
                    for d in DOORS:
                        # If found the right door and it's not in motion already
                        if x == d.x and y == d.y:
                            d.state = 1
                            break
                elif tile_id[0] == 'Wall' and tile_id[1] == 'End-trigger':
                    TILEMAP[y][x] += 1  # Change triggerblock texture
                    #level_end()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if WEAPON_MODEL.weapon.mag_ammo and not WEAPON_MODEL.reloading and not WEAPON_MODEL.switching:
                    WEAPON_MODEL.shooting = True
            elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.reloading:
                if event.button == 4:  # Mousewheel up
                    if PLAYER.weapon_nr > 1:  # Can't go under 1
                        WEAPON_MODEL.switching = -1
                if event.button == 5:  # Mousewheel down
                    if PLAYER.weapon_nr < len(WEAPONS) - 1:
                        WEAPON_MODEL.switching = 1


def update_gameobjects():
    # Function made for updating dynamic game objects every frame
    for d in DOORS:
        d.move()
    for e in ENEMIES:
        e.update()
    WEAPON_MODEL.update()


def draw_frame():
    # Sorting objects by perp_dist so those further away are drawn first
    to_draw = WALLS + ENEMIES + OBJECTS
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)
    for obj in to_draw:
        obj.draw(DISPLAY)


def load_enemies(tilemap, tile_values_info):
    # Scan through all of tilemap and
    # create a enemy if the tile id is correct
    enemies = []
    for row in range(len(tilemap)):
        for column in range(len(tilemap[row])):
            tile_id = tile_values_info[tilemap[row][column]][0]
            if tile_id[0] == 'Enemy':
                spritesheet = tile_values_info[tilemap[row][column]][1]
                pos = (column + 0.5, row + 0.5)
                enemies.append(Enemy(spritesheet, pos))
                tilemap[row][column] = 0  # Clears tile
    return enemies


def load_level(level_nr, tile_values_info):
    # Decoding tilemap
    with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
        row = f.readline().replace('\n', '').split(',')
        row = [float(i) for i in row]
        player = Player((row[0], row[1]), row[2])  # Creates player

        background_colours = []
        for _ in range(2):
            row = f.readline().replace('\n', '').split(',')  # Split the line to a list and get rid of newline (\n)
            row = [int(i) for i in row]  # Turn all number strings to an int
            background_colours.append(tuple(row))

        tilemap = []
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            tilemap.append(row)

    # Run pathfinding setup function
    pathfinding.setup(tilemap, tile_values_info)

    return player, background_colours, tilemap, []  # <-- empty doors list


def send_rays():
    global WALLS
    WALLS = []

    global OBJECTS
    OBJECTS = []

    for c, d in enumerate(DOORS):
        if d.state == 0:  # If door not in motion
            del DOORS[c]

    # Checking if player is standing on an object
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:  # If anything under player
        tile_id = TILE_VALUES_INFO[tile_value][0]
        if tile_id[1] == 'Ammo':
            if PLAYER.ammo < 99:
                PLAYER.ammo += 6
                if PLAYER.ammo > 99:
                    PLAYER.ammo = 99
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0  # "Deletes" object
        elif tile_id[1] == 'Health':
            if PLAYER.hp < 100:
                PLAYER.hp += 20
                if PLAYER.hp > 100:
                    PLAYER.hp = 100
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0  # "Deletes" object
        OBJECTS.append(Object((int(PLAYER.x), int(PLAYER.y)), tile_value))

    # Sending rays
    for i in range(len(RAYANGLES)):
        # Get the rayangle that's going to be raycasted
        rayangle = fixed_angle(PLAYER.viewangle + RAYANGLES[i])

        # Get values from raycast()
        tile_value, ray_x, ray_y, column = raycast(rayangle, (PLAYER.x, PLAYER.y))
        delta_x = ray_x - PLAYER.x
        delta_y = ray_y - PLAYER.y

        # Calculate perpendicular distance (needed to avoid fisheye effect)
        perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        # Get wall texture
        for d in DOORS:
            # Ray x and y abs(distances) to door center position
            x_diff = abs(d.x + 0.5 - ray_x)
            y_diff = abs(d.y + 0.5 - ray_y)
            if (x_diff == 0.5 and y_diff <= 0.5) or (y_diff == 0.5 and x_diff <= 0.5):
                texture = DOOR_SIDE_TEXTURE
                break
        else:
            texture = TILE_VALUES_INFO[tile_value][1]

        # Create Wall object
        WALLS.append(Wall(perp_dist, texture, column, i))


def raycast(rayangle, pos):
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

    ray_x, ray_y = pos
    tan_rayangle = tan(rayangle)  # Calculating tay(rayangle) once to not calculate it over every step

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
        # Every loop it blindly calculates vertical* gridline interception_y and checks it's distance
        # to determine the interception type and to calculate other varibles depending on that interception type
        # Originally it remembered previous interception type to calculate the new one
        # but doing it this way turns out to be faster
        #
        # *It calculates vertical gridline interception by default bc in those calculations
        # there are no divisions which could bring up ZeroDivisionError

        interception_y = (A - x_offset) * tan_rayangle
        if int(ray_y - y_offset) == int(ray_y + interception_y):
            # Hitting vertical gridline ( | )
            interception_x = A - x_offset

            ray_x += interception_x
            ray_y += interception_y
            map_y = int(ray_y)
            map_x = int(ray_x) + (A - 1)
            side = 0

        else:
            # Hitting horizontal gridline ( -- )
            interception_x = (B - y_offset) / tan_rayangle
            interception_y = B - y_offset

            ray_x += interception_x
            ray_y += interception_y
            map_y = int(ray_y) + (B - 1)
            map_x = int(ray_x)
            side = 1

        tile_value = TILEMAP[map_y][map_x]
        if tile_value != 0:  # If ray touching something

            tile_id = TILE_VALUES_INFO[tile_value][0]

            if tile_id[0] == 'Object':
                obj = Object((map_x, map_y), tile_value)
                for o in OBJECTS:
                    if o == obj:
                        break
                else:
                    OBJECTS.append(obj)
                continue

            if tile_id[0] == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                # Add door to DOORS if it's not in it already
                door = Door((map_x, map_y), tile_value)
                for d in DOORS:
                    if d == door:
                        door = d
                        break
                else:
                    DOORS.append(door)

                if side == 0:  # If vertical ( | )
                    interception_y = (-0.5 + A) * tan_rayangle
                    offset = ray_y + interception_y - int(ray_y + interception_y)
                    if int(ray_y - y_offset) == int(ray_y + interception_y) and offset > door.opened_state:
                        ray_x += (-0.5 + A)
                        ray_y += interception_y
                        column = int(TEXTURE_SIZE * (offset - door.opened_state))
                    else:
                        continue

                else:  # If horizontal ( -- )
                    interception_x = (-0.5 + B) / tan_rayangle
                    offset = ray_x + interception_x - int(ray_x + interception_x)
                    if int(ray_x - x_offset) == int(ray_x + interception_x) and offset > door.opened_state:
                        ray_x += interception_x
                        ray_y += (-0.5 + B)
                        column = int(TEXTURE_SIZE * (offset - door.opened_state))
                    else:
                        continue

            else:  # If anything other but a door (door sides count here aswell)
                if side == 0:
                    offset = abs(ray_y - int(ray_y) - (1 - A))
                else:
                    offset = abs(ray_x - int(ray_x) - B)
                column = int(TEXTURE_SIZE * offset)

            if side == 0:
                column += TEXTURE_SIZE  # Makes block sides different

            return tile_value, ray_x, ray_y, column


def fixed_angle(angle):
    # Function made for angles to never go over +-pi
    # For example 3.18 will be turned to -3.10, bc it's 0.04 over pi

    if angle > pi:  # 3.14+
        angle -= 2 * pi
    elif angle < -pi:  # 3.14-
        angle += 2 * pi

    return angle


def movement():
    # Checks for player movement (WASD)
    # Also returns player direction vector to use elsewhere

    keys_pressed = pygame.key.get_pressed()
    player_dir_x = cos(PLAYER.viewangle)
    player_dir_y = sin(PLAYER.viewangle)

    # Vector based movement, bc otherwise player could move faster diagonally
    if keys_pressed[K_w] or keys_pressed[K_a] or keys_pressed[K_s] or keys_pressed[K_d]:
        movement_x = 0
        movement_y = 0
        if keys_pressed[K_w]:
            movement_x += player_dir_x
            movement_y += player_dir_y

        if keys_pressed[K_a]:
            movement_x += player_dir_y
            movement_y += -player_dir_x

        if keys_pressed[K_s]:
            movement_x += -player_dir_x
            movement_y += -player_dir_y

        if keys_pressed[K_d]:
            movement_x += -player_dir_y
            movement_y += player_dir_x

        # Needed for normalize() function
        movement_vector = np.asarray([[movement_x, movement_y]])

        # Removes the errors where pressing both (or all) opposite movement keys, player would still move,
        # bc the movement vector would not be a perfect (0, 0)
        if abs(movement_vector[0][0]) + abs(movement_vector[0][1]) > 0.1:

            # Normalized vector
            normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
            movement_x = normalized_vector[0] * PLAYER.speed
            movement_y = normalized_vector[1] * PLAYER.speed

            PLAYER.move(movement_x, movement_y)

    return player_dir_x, player_dir_y


def draw_background():
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[0], ((0,       0), (D_W, D_H / 2)))  # Ceiling
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[1], ((0, D_H / 2), (D_W, D_H / 2)))  # Floor


def draw_hud():
    def dynamic_colour(current, max):
        ratio = current / max  # 1 is completely green, 0 completely red
        if ratio < 0.5:
            red = 255  # Red stays
            green = int(ratio * 2 * 255)
        else:
            ratio = 1 - ratio
            green = 255  # Green stays
            red = int(ratio * 2 * 255)

        return (red, green, 0)

    # FPS counter
    text_surface = GAME_FONT.render(str(round(CLOCK.get_fps())), False, (0, 255, 0))
    DISPLAY.blit(text_surface, (4, 4))

    # Crosshair
    CROSSHAIR.draw(DISPLAY)

    # Weapon model
    WEAPON_MODEL.draw(DISPLAY)

    # Weapon name
    weapon_name = '{}: '.format(WEAPON_MODEL.weapon.name)
    weapon_name_surface = GAME_FONT.render(weapon_name, False, (255, 255, 255))
    DISPLAY.blit(weapon_name_surface, (4, D_H - 32))

    # Weapon ammo
    if WEAPON_MODEL.weapon.ammo_unlimited:
        total_ammo = 'Unlimited'
    else:
        total_ammo = PLAYER.ammo
    weapon_ammo = '{}/{}'.format(WEAPON_MODEL.weapon.mag_ammo, total_ammo)
    weapon_ammo_surface = GAME_FONT.render(weapon_ammo, False, dynamic_colour(WEAPON_MODEL.weapon.mag_ammo, WEAPON_MODEL.weapon.mag_size))
    DISPLAY.blit(weapon_ammo_surface, (4 + weapon_name_surface.get_width(), D_H - 32))

    # Player hp
    hp_text_surface = GAME_FONT.render('HP: ', False, (255, 255, 255))
    DISPLAY.blit(hp_text_surface, (4, D_H - 64))

    hp_amount_surface = GAME_FONT.render(str(PLAYER.hp), False, dynamic_colour(PLAYER.hp, 100))
    DISPLAY.blit(hp_amount_surface, (4 + hp_text_surface.get_width(), D_H - 64))


def get_rayangles(rays_amount):
    # Returns a list of angles which raycast() is going to use to add to player's viewangle
    # Because these angles do not depend on player's viewangle, they are calculated even before the main loop starts
    #
    # It calculates these angles so that each angle's end position is on the camera plane,
    # equal distance away from the previous one
    #
    # Could be made faster, but since it's calculated only once before main loop, readability is more important
    # Note that in 2D rendering, camera plane is actually a single line
    # Also FOV has to be < pi (and not <= pi) for it to work properly

    rayangles = []
    camera_plane_len = 1
    camera_plane_start = -camera_plane_len / 2
    camera_plane_step = camera_plane_len / rays_amount

    camera_plane_dist = (camera_plane_len / 2) / tan(FOV / 2)
    for i in range(rays_amount):
        camera_plane_pos = camera_plane_start + i * camera_plane_step

        angle = atan2(camera_plane_pos, camera_plane_dist)
        rayangles.append(angle)

    return rayangles, camera_plane_len, camera_plane_dist

if __name__ == '__main__':
    from math import *
    import random

    import numpy as np
    from sklearn.preprocessing import normalize

    import pygame
    from pygame.locals import *

    import raycasting.main.tilevaluesinfo as tilevaluesinfo
    import raycasting.main.pathfinding as pathfinding

    # Game settings
    D_W = 1024
    D_H = 800
    FOV = pi / 2  # = 90 degrees
    RAYS_AMOUNT = int(D_W / 2)  # Drawing frequency across the screen / Rays casted each frame
    SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved horizontally

    # Pygame stuff
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    TEXTURE_SIZE = 64

    TILE_VALUES_INFO,\
    ENEMY_INFO,\
    DOOR_SIDE_TEXTURE = tilevaluesinfo.get(TEXTURE_SIZE)

    RAYANGLES,\
    CAMERA_PLANE_LEN,\
    CAMERA_PLANE_DIST = get_rayangles(RAYS_AMOUNT)

    PLAYER,\
    BACKGROUND_COLOURS,\
    TILEMAP,\
    DOORS = load_level(1, TILE_VALUES_INFO)

    ENEMIES = load_enemies(TILEMAP, TILE_VALUES_INFO)
    WEAPONS = load_weapons()
    WEAPON_MODEL = WeaponModel()
    CROSSHAIR = Crosshair(2, 6, 6, (0, 255, 0))

    GAME_FONT = pygame.font.Font('../LCD_Solid.ttf', 32)

    ###
    Drawable.constant = 0.6 * D_H
    Wall.width = int(D_W / RAYS_AMOUNT)
    ###

    RUNNING = True
    while RUNNING:
        PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
        PLAYER.dir_x, PLAYER.dir_y = movement()

        update_gameobjects()
        events()

        draw_background()
        send_rays()
        draw_frame()
        draw_hud()

        pygame.display.flip()
        CLOCK.tick(30)

    pygame.quit()
