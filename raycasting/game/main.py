# TO DO:
# Enemy hitscan
# Enemy continuous shooting from point blank
# Level end system
# Level editor sky texture choosing
# Make enemies alert other enemies in the same room

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians
# Objects are in OBJECTS list only if that object's cell is visible to player
# Enemies are in ENEMIES list at all times bc moving objects are harder to optimize
# Wall texture files require two textures side by side (even if they are going to be the same),
# bc raycast() is going to pick one based on the side of the interception
# All timed events are tick based,
# meaning that changing fps will change timer time
# Every level folder can be equipped with a sky.png texture,
# which will then be drawn dynamically instead of drawing just a plain ceiling colour
# DOORS list contains all doors currently visible or in motion


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

    def hitscan(self, weapon):
        # An instant shot detection system
        # Applies to everything but projectile weapons

        # Find all shottable enemies in ENEMIES list
        shottable_enemies = []
        for e in ENEMIES:
            # If enemy not dead and player can see him
            if not e.dead and can_see((PLAYER.x, PLAYER.y), (e.x, e.y), PLAYER.viewangle, FOV):
                shottable_enemies.append(e)
        shottable_enemies.sort(key=lambda x: x.dist_squared)  # Makes hit register for closest enemy

        for e in shottable_enemies:
            enemy_center_display_x = e.display_x + (e.width / 2)
            x_offset = abs(H_W - enemy_center_display_x)
            hittable_offset = e.hittable_amount / 2 * e.width
            if hittable_offset > x_offset:  # If crosshair more or less on enemy
                if not weapon.melee:
                    e.hurt()
                elif e.dist_squared <= 2:  # Assuming that melee weapons don't hit enemies more than sqrt(2) = 1.4 units away
                    e.hurt(3)  # Assuming that melee weapons deal 3 damage
                break

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
        self.update()

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

            if self.column == weapon.shot_column:
                # Time to shoot
                if not weapon.melee:
                    weapon.mag_ammo -= 1
                if not weapon.projectile:
                    PLAYER.hitscan(weapon)
                else:
                    p = Projectile((PLAYER.x, PLAYER.y), PLAYER.viewangle, weapon.projectile_speed, weapon.projectile)
                    PROJECTILES.append(p)

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
            PLAYER.weapon_nr = self.switching  # Switches weapon model when halfway through

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
        cell_w = cell_h = 512
        weapon_image = self.weapon.weapon_sheet.subsurface(cell_w * self.column, 0, cell_w, cell_h)
        surface.blit(weapon_image, ((D_W - cell_w) / 2, D_H - cell_h + self.draw_y))


class Door:
    speed = 0.05
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

            elif self.state == 2:  # Staying open
                self.ticks += 1
                if self.ticks >= Door.open_ticks:  # If time for door to close
                    # Checking if player is not in door's way
                    safe_dist = 0.5 + Player.half_hitbox
                    if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            elif self.state == 3:  # Closing
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

    # Amount of ticks that every image of animation is going to be shown
    # The delay of which images are going to change
    animation_ticks = 5

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
                    try:
                        # Getting sprite column out of image
                        sprite_column = self.image.subsurface(column, 0, 1, self.image.get_height())

                        # Scaling that column
                        sprite_column = pygame.transform.scale(sprite_column, (ceil(column_width), self.height))

                        # Blitting that column
                        surface.blit(sprite_column, (column_left_side, self.display_y))
                    except pygame.error:  # If scaling size is too big (happens rarely if player too close to enemy)
                        break  # End drawing sprite

    def calc_display_xy(self, angle_from_player, y_multiplier=1.0):
        # In order to calculate sprite's correct display x/y position, we need to calculate it's camera plane position
        # NOTE: atan2(delta_y, delta_x) is the angle from player to sprite

        camera_plane_pos = CAMERA_PLANE_LEN / 2 + tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE_DIST

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H  - self.height * y_multiplier) / 2


class Projectile(Drawable, Sprite):
    def __init__(self, pos, angle, speed, images):
        self.angle = angle
        self.speed = speed
        self.x, self.y = pos
        self.x += cos(self.angle) * 0.25
        self.y += sin(self.angle) * 0.25
        self.images = images

        self.column = random.randint(0, 2)
        self.damage = self.column + 1
        self.ticks = 0
        self.y_multiplier = 0.55  # Makes projectile draw at gun level
        self.hit = False

        self.update()

    def update(self):
        # Check wall collision
        if TILEMAP[int(self.y)][int(self.x)] > 0:
            self.hit = True

        else:
            for e in ENEMIES:  # Check enemy collision
                if not e.dead:
                    squared_dist = (e.x - self.x)**2 + (e.y - self.y)**2
                    if squared_dist < 0.03:
                        self.hit = True
                        e.hurt(self.damage)
                        break
            else:
                self.ticks += 1
                if self.ticks == Sprite.animation_ticks:
                    self.ticks = 0
                    self.column += 1
                    if self.column > 2:
                        self.column = 0
                self.x += cos(self.angle) * self.speed
                self.y += sin(self.angle) * self.speed

        # Update image for drawing
        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        angle_from_player = atan2(delta_y, delta_x)

        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            self.image = self.images.subsurface(self.column * TEXTURE_SIZE, 0, TEXTURE_SIZE, TEXTURE_SIZE)

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            self.calc_display_xy(angle_from_player, self.y_multiplier)


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

    # Stationary enemy turning speed
    # Radians per tick as always
    turning_speed = 0.1

    def __init__(self, spritesheet, pos):
        self.x, self.y = self.home = pos
        self.angle = 0  # Enemy actual angle
        self.wanted_angle = 0  # Angle to which enemy is turning

        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.column = 0  # Spritesheet column

        self.path = []  # Enemy running path
        self.shooting = False
        self.dead = False
        self.hit = False

        # Take attributes from ENEMY_INFO based on spritesheet (enemy type)
        # What each attribute means see graphics.py get_enemy_info() enemy_info dictionary description
        self.name, self.hp, self.speed, self.shooting_range, self.memory, self.patience, self.hittable_amount = ENEMY_INFO[self.sheet]

        # Timed events tick (frames passed) variables
        self.anim_ticks = 0  # Time passed during animation
        self.last_saw_ticks = self.memory  # Time passed when the enemy last saw the player
        self.stationary_ticks = 0  # Time enemy has stayed stationary/without moving (turning counts as moving)
        self.last_hit_anim_ticks = Sprite.animation_ticks  # Makes enemies not freeze when they're shot very often

    def get_look_angles(self):
        # Creates a list of angles that are going to be chosen by random when stationary every once in a while
        # Angles which enemy can see more are chosen more often
        self.look_angles = []
        rayangles = [x/10*pi for x in range(10, -10, -1)]  # 20 different viewangles should be enough
        for rayangle in rayangles:

            ray_x, ray_y = raycast(rayangle, (self.x, self.y))[1:3]  # <-- Only selects ray_x/ray_y
            ray_dist = sqrt((ray_x - self.x)**2 + (ray_y - self.y)**2)

            for _ in range(int(ray_dist)):
                self.look_angles.append(rayangle)

    def get_home_room(self):
        # Makes a self.home_room list which contains all the map points in his room

        def get_unvisited(pos):
            # Gets new unvisited points
            all_points = visited + unvisited
            for x in range(-1, 2):  # -1, 0, 1
                for y in range(-1, 2):  # -1, 0, 1
                    pos_x, pos_y = (pos[0] + x, pos[1] + y)
                    if (pos_x, pos_y) not in all_points and TILEMAP[pos_y][pos_x] <= 0:
                        unvisited.append((pos_x, pos_y))

        visited = [(int(self.x), int(self.y))]
        unvisited = []
        get_unvisited((int(self.x), int(self.y)))

        while unvisited:  # While there is unscanned points
            current = unvisited[0]  # Get new point
            del unvisited[0]  # Delete it from unvisited bc it's about to get visited
            visited.append(current)  # Add point to visited
            get_unvisited(current)  # Scan new points from that location

        self.home_room = visited

    def hurt(self, damage=1):
        self.hp -= damage  # Take hp away from enemy
        self.shooting = False  # Cancel shooting action
        if self.hp <= 0:  # If dead
            self.hit = True  # Mark as hit
            self.row = 5  # Choose death/hurt animation row
            self.anim_ticks = 0  # Reset animation ticks
            self.dead = True  # Mark as dead
            self.column = 0  # Choose first death animation frame
        elif self.last_hit_anim_ticks >= Sprite.animation_ticks - 2:  # If not dead and enough time passed to show new hit animation
            self.hit = True
            self.row = 5
            self.anim_ticks = 0
            self.last_hit_anim_ticks = 0

    def shoot(self):
        # Hitscan system stolen straight from Wolfenstein 3D source code
        # Player shot hit and damage logic
        pass

    def update(self):

        # Enemy door opening system
        # If door underneath enemy,
        # create a door obj in that location if it isn't there already
        # and start opening it immediately
        tile_value = TILEMAP[int(self.y)][int(self.x)]
        if TILE_VALUES_INFO[tile_value][0][0] == 'Door':
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
        angle_from_player = atan2(delta_y, delta_x)

        self.dist_squared = delta_x**2 + delta_y**2  # Used in player's shot detection

        if self.shooting:
            self.row = 6
            self.anim_ticks += 1
            self.column = int(self.anim_ticks / Sprite.animation_ticks)
            if self.anim_ticks == Sprite.animation_ticks * 2:
                self.shoot()
            if self.column > 2:
                self.column = 2
                self.shooting = False

                self.anim_ticks = 0
                self.last_saw_ticks = 0
                self.stationary_ticks = 0

        elif not self.hit:
            can_see_player = can_see((self.x, self.y), (PLAYER.x, PLAYER.y), self.angle, FOV)
            self.wanted_angle = atan2(-delta_y, -delta_x)

            if can_see_player:
                self.last_saw_ticks = 0
            elif self.last_saw_ticks < self.memory:
                self.last_saw_ticks += 1
            elif self.dist_squared > 2:  # If dist more than sqrt(2) == 1.4
                self.wanted_angle = self.angle  # Reset wanted_angle ; Don't look at player

            # Turn towards wanted angle
            if self.angle != self.wanted_angle:
                self.stationary_ticks = 0

                difference = (self.wanted_angle + pi) - (self.angle + pi)
                if difference < 0:
                    difference += 2*pi

                if difference < pi:
                    self.angle += Enemy.turning_speed
                else:
                    self.angle -= Enemy.turning_speed

                # If self.angle close enough:
                # Finish turning
                if abs(self.angle - self.wanted_angle) < Enemy.turning_speed:
                    self.angle = self.wanted_angle

            # Update last hit animation ticks
            if self.last_hit_anim_ticks != Sprite.animation_ticks:
                self.last_hit_anim_ticks += 1

            if not self.path:
                # Scope logic:
                #   If enemy can see player:
                #       Set path to player
                #   Elif enemy's been stationary for a while:
                #       Choose a new action
                self.stationary_ticks += 1
                if can_see_player or self.last_saw_ticks < self.memory:
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))

                elif self.stationary_ticks > self.patience:
                    if (self.x, self.y) == self.home:
                        # If at home:
                        # Either look at semi-random angle
                        # Or go to a random location in his room
                        if random.randint(0, 1) == 0:
                            self.wanted_angle = random.choice(self.look_angles)
                        else:
                            self.path = pathfinding.pathfind((self.x, self.y), random.choice(self.home_room))
                    else:
                        self.path = pathfinding.pathfind((self.x, self.y), self.home)

            if self.path:
                self.stationary_ticks = 0
                step_x, step_y = self.path[0]

                # If other enemy(s) in step tile:
                # Empty path and don't step
                # Else:
                # Make a step
                for e in ENEMIES:
                    if not e.dead and e.home != self.home and (int(e.x), int(e.y)) == (step_x, step_y):
                        self.path = []
                        break
                else:
                    step_x += 0.5  # Centers tile pos
                    step_y += 0.5

                    self.angle = self.wanted_angle = atan2(step_y - self.y, step_x - self.x)
                    self.x += cos(self.angle) * self.speed
                    self.y += sin(self.angle) * self.speed

                    # Could recalculate delta_x/delta_y here but it makes next to no difference

                    # If enemy close enough to the path step
                    if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                        self.x = step_x
                        self.y = step_y
                        # If close enough to player, start shooting in next frame
                        if can_see_player and self.dist_squared < self.shooting_range ** 2:
                            self.shooting = True
                            self.path = []
                        elif can_see_player or self.last_saw_ticks < self.memory:
                            self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
                        else:
                            del self.path[0]
                            # Turn towards player when path finished
                            if not self.path:
                                self.angle = atan2(-delta_y, -delta_x)

            # Find the right spritesheet column
            angle = fixed_angle(-angle_from_player + self.angle) + pi  # +pi to get rid of negative values
            self.column = round(angle / (pi / 4))
            if self.column == 8:
                self.column = 0

            # Find the right spritesheet row
            if self.path:  # If movement
                if self.row == 0 or self.row > 4:
                    self.row = 1
                # Cycle through running animations
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.row += 1
                    if self.row == 5:
                        self.row = 1
            else:  # If not movement
                self.anim_ticks = 0
                self.row = 0

        else:
            if self.dead:  # If dead/dying
                if self.column < 4:  # 4 is the final death animation frame ; If death animation not completed
                    self.anim_ticks += 1
                    if self.anim_ticks == Sprite.animation_ticks:
                        self.anim_ticks = 0
                        self.column += 1
            else:  # If hit
                self.column = 7
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.hit = False
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))

        # Calculate perpendicular distance
        # If it's more than 0 ; If enemy is going to be drawn:
        # Update image for drawing
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            self.image = self.sheet.subsurface(self.column * TEXTURE_SIZE, self.row * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)

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
        self.visible = False

    def draw(self, surface):
        if self.visible:
            pygame.draw.line(surface, self.colour, (H_W + self.gap, H_H), (H_W + self.gap + self.len, H_H), self.width)
            pygame.draw.line(surface, self.colour, (H_W - self.gap, H_H), (H_W - self.gap - self.len, H_H), self.width)
            pygame.draw.line(surface, self.colour, (H_W, H_H + self.gap), (H_W, H_H + self.gap + self.len), self.width)
            pygame.draw.line(surface, self.colour, (H_W, H_H - self.gap), (H_W, H_H - self.gap - self.len), self.width)


def events():
    global RUNNING

    weapon = WEAPON_MODEL.weapon

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                RUNNING = False

            elif event.key == K_F1:
                CROSSHAIR.visible = not CROSSHAIR.visible

            elif event.key == K_r and not weapon.melee:
                # If magazine not full and weapon not shooting
                if weapon.mag_ammo < weapon.mag_size and not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
                    if weapon.ammo_unlimited:
                        WEAPON_MODEL.reloading = True
                    elif PLAYER.ammo:
                        WEAPON_MODEL.reloading = True

            elif event.key == K_e:
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
                    TILEMAP[y][x] += 1  # Change trigger block texture
                    #level_end()

            elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.reloading:
                key = pygame.key.name(event.key)
                numbers = (str(x) for x in range(1, 10))  # Skips 0 bc that can't be weapon slot
                if key in numbers:
                    key = int(key)
                    # If requested weapon not equipped already and key index in WEAPONS
                    if key != PLAYER.weapon_nr and key <= len(WEAPONS) - 1:
                        WEAPON_MODEL.switching = key

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not WEAPON_MODEL.reloading and not WEAPON_MODEL.switching:
                    if weapon.mag_ammo or weapon.melee:
                        WEAPON_MODEL.shooting = True
            elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.reloading:
                if event.button == 4:  # Mousewheel up
                    if PLAYER.weapon_nr > 1:  # Can't go under 1
                        WEAPON_MODEL.switching = PLAYER.weapon_nr - 1
                if event.button == 5:  # Mousewheel down
                    if PLAYER.weapon_nr < len(WEAPONS) - 1:
                        WEAPON_MODEL.switching = PLAYER.weapon_nr + 1


def can_see(from_, to, viewangle, fov):
    # Universal function for checking if it's possible to see one point from another in tilemap
    # Returns True if end point visible, False if not visible

    start_x, start_y = from_
    end_x, end_y = to

    angle_to_end = atan2(end_y - start_y, end_x - start_x)
    if abs(angle_to_end - viewangle) < fov / 2:  # If end position inside viewangle

        # Check if there is something between enemy and player
        ray_x, ray_y = raycast(angle_to_end, from_)[1:3]  # [1:3] only selects ray_x/ray_y
        ray_dist_squared = (start_x - ray_x) ** 2 + (start_y - ray_y) ** 2
        end_dist_squared = (start_x - end_x) ** 2 + (start_y - end_y) ** 2
        if ray_dist_squared > end_dist_squared:  # If interception farther than end point ; If no wall in front of end point
            return True
    return False


def update_gameobjects():
    # Function made for updating dynamic game objects every frame
    for c, d in enumerate(DOORS):
        d.move()
        if d.state == 0:
            del DOORS[c]
    for e in ENEMIES:
        e.update()
    for c, p in enumerate(PROJECTILES):
        p.update()
        if p.hit:
            del PROJECTILES[c]
    WEAPON_MODEL.update()


def draw_frame():
    # Sorting objects by perp_dist so those further away are drawn first
    to_draw = WALLS + ENEMIES + OBJECTS + PROJECTILES
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

    # Process some stuff after enemies have been cleared from tilemap
    for e in enemies:
        e.get_look_angles()
        e.get_home_room()

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

        # Get sky texture if there is one
        try:
            sky_texture = pygame.image.load('../levels/{}/sky.png'.format(level_nr)).convert()
        except pygame.error:
            sky_texture = None
        else:
            sky_texture = pygame.transform.scale(sky_texture, (D_W * 4, H_H))

        tilemap = []
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            tilemap.append(row)

    # Run pathfinding setup function
    pathfinding.setup(tilemap, tile_values_info)

    return player, background_colours, sky_texture, tilemap, [], []  # <-- empty doors and projectiles lists, need to reset these if level changes


def send_rays():
    global WALLS
    WALLS = []

    global OBJECTS
    OBJECTS = []

    # Checking if player is standing on an object
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:  # If anything under player
        tile_id = TILE_VALUES_INFO[tile_value][0]
        if tile_id[1] == 'Ammo':
            if PLAYER.ammo < 999:
                PLAYER.ammo += 10
                if PLAYER.ammo > 999:
                    PLAYER.ammo = 999
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


def raycast(rayangle, start_pos):
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

    ray_x, ray_y = start_pos
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
    if SKY_TEXTURE:
        # x_offset is a value ranging from 0 to 1
        x_offset = (PLAYER.viewangle + pi) / (2*pi)
        x = x_offset * SKY_TEXTURE.get_width()

        if x_offset <= 0.75:
            # Sky texture can be drawn as one image
            sky = SKY_TEXTURE.subsurface(x, 0, D_W, H_H)
            DISPLAY.blit(sky, (0, 0))
        else:
            # Sky texture needs to be drawn as two separate parts
            sky_left = SKY_TEXTURE.subsurface(x, 0, SKY_TEXTURE.get_width() - x, H_H)
            sky_right = SKY_TEXTURE.subsurface(0, 0, D_W - sky_left.get_width(), H_H)
            DISPLAY.blit(sky_left, (0, 0))
            DISPLAY.blit(sky_right, (sky_left.get_width(), 0))
    else:
        pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[0], ((0, 0), (D_W, H_H)))  # Ceiling
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[1], ((0, H_H), (D_W, H_H)))  # Floor


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

    x_safezone = 6  # In pixels

    # Simulates blinking effect
    global ALPHA
    ALPHA -= 15
    if ALPHA == -255:
        ALPHA = 255

    # FPS counter
    text_surface = GAME_FONT.render(str(round(CLOCK.get_fps())), False, (0, 255, 0))
    DISPLAY.blit(text_surface, (3, 3))

    # Crosshair
    CROSSHAIR.draw(DISPLAY)

    # Weapon HUD
    WEAPON_MODEL.draw(DISPLAY)
    current_weapon = WEAPON_MODEL.weapon

    weapon_name_surface = GAME_FONT.render(str(current_weapon.name), False, (255, 255, 255))
    if current_weapon.melee:
        weapon_ammo_surface = GAME_FONT.render('--/--', False, (0, 255, 0))
    else:
        if not WEAPON_MODEL.reloading:
            if current_weapon.ammo_unlimited:
                total_ammo = 'Unlimited'
            else:
                total_ammo = PLAYER.ammo

            weapon_ammo = '{}/{}'.format(current_weapon.mag_ammo, total_ammo)

            if current_weapon.mag_ammo:
                ALPHA = 255  # Resets blinking
                weapon_ammo_surface = GAME_FONT.render(weapon_ammo, False, dynamic_colour(current_weapon.mag_ammo, current_weapon.mag_size))
            else:
                weapon_ammo_surface = GAME_FONT.render(weapon_ammo, False, (255, 0, 0), (0, 0, 0))  # Set background to black
                weapon_ammo_surface.set_colorkey((0, 0, 0))  # Tell program to treat black as transparent
                weapon_ammo_surface.set_alpha(abs(ALPHA))
        else:
            weapon_ammo_surface = GAME_FONT.render('Reloading', False, (255, 0, 0), (0, 0, 0))  # Set background to black
            weapon_ammo_surface.set_colorkey((0, 0, 0))  # Tell program to treat black as transparent
            weapon_ammo_surface.set_alpha(abs(ALPHA))

    DISPLAY.blit(weapon_name_surface, (D_W - weapon_name_surface.get_width() - x_safezone, D_H - 64))
    DISPLAY.blit(weapon_ammo_surface, (D_W - weapon_ammo_surface.get_width() - x_safezone, D_H - 32))

    # Player hp HUD
    hp_text_surface = GAME_FONT.render('HP:', False, (255, 255, 255))
    hp_amount_surface = GAME_FONT.render(str(PLAYER.hp), False, dynamic_colour(PLAYER.hp, 100))
    DISPLAY.blit(hp_text_surface, (x_safezone, D_H - 64))
    DISPLAY.blit(hp_amount_surface, (x_safezone, D_H - 32))


def get_rayangles(rays_amount):
    # Returns a list of angles which raycast() is going to use to add to player's viewangle
    # Because these angles do not depend on player's viewangle, they are calculated even before the game loop starts
    #
    # It calculates these angles so that each angle's end position is on the camera plane,
    # equal distance away from the previous one
    #
    # Could be made faster, but since it's calculated only once before game loop, readability is more important
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
    import sys

    from math import *
    import random

    import numpy as np
    from sklearn.preprocessing import normalize

    import pygame
    from pygame.locals import *

    import raycasting.game.graphics as graphics
    import raycasting.game.pathfinding as pathfinding

    # Game settings
    D_W = 800
    D_H = 600
    H_W = int(D_W / 2)  # Half width
    H_H = int(D_H / 2)  # Half height
    FOV = pi / 2  # = 90 degrees
    RAYS_AMOUNT = H_W  # Drawing frequency across the screen / Rays casted each frame
    SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved horizontally

    # Pygame stuff
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    # Font
    GAME_FONT = pygame.font.Font('../font/LCD_Solid.ttf', 32)
    ALPHA = 255  # Text transparency value used to create blinking texts in draw_hud()

    TEXTURE_SIZE = 64

    DOOR_SIDE_TEXTURE = graphics.get_door_side_texture(sys, pygame)
    ENEMY_INFO = graphics.get_enemy_info(sys, pygame)
    TILE_VALUES_INFO = graphics.get_tile_values_info(sys, pygame, TEXTURE_SIZE, ENEMY_INFO)
    WEAPONS = graphics.get_weapons(sys, pygame)

    RAYANGLES,\
    CAMERA_PLANE_LEN,\
    CAMERA_PLANE_DIST = get_rayangles(RAYS_AMOUNT)

    PLAYER,\
    BACKGROUND_COLOURS,\
    SKY_TEXTURE,\
    TILEMAP,\
    DOORS,\
    PROJECTILES = load_level(1, TILE_VALUES_INFO)

    ENEMIES = load_enemies(TILEMAP, TILE_VALUES_INFO)

    WEAPON_MODEL = WeaponModel()
    CROSSHAIR = Crosshair(4, 6, 4, (0, 200, 200))

    # Make class constants
    Drawable.constant = 0.6 * D_H
    Wall.width = int(D_W / RAYS_AMOUNT)

    RUNNING = True
    while RUNNING:
        PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
        PLAYER.dir_x, PLAYER.dir_y = movement()

        events()
        update_gameobjects()

        draw_background()
        send_rays()
        draw_frame()
        draw_hud()

        pygame.display.flip()
        CLOCK.tick(30)

    pygame.quit()
