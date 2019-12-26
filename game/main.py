# TO DO:
# Create levels
# Level number hud
# Send messages when trying to unlock locked doors without key, picking stuff up
# Add render_text as a function

# NOTES:
# Game's tick rate is at 30
# Due to poor optimization, big open areas will drop fps
# All timed events are tick based
# All angles are in radians
# Enemies can travel through Dynamic and Locked doors, but not Static or Boss doors
# Killing a boss gives the player a key
# There is no support for multiple bosses in one level

# Sound Channels:
# 0 = door and pickup sounds
# 1 = player's weapon sounds
# 2 - 6 = normal enemy sounds
# 7 = boss sounds


class Player:
    max_hp = 100
    speed = 0.15  # Must be < half_hitbox, otherwise player can clip through walls
    hitbox_size = 0.4
    half_hitbox = hitbox_size / 2

    def __init__(self):
        self.weapon_nr = 1
        self.saved_weapon_loadout = [1]

    def setup(self, pos, angle):
        self.x = pos[0] + 0.0000001
        self.y = pos[1] + 0.0000001
        self.viewangle = angle + 0.0000001
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        self.hp = Player.max_hp
        self.has_key = False

        self.weapon_loadout = self.saved_weapon_loadout[:]
        if self.weapon_nr not in self.weapon_loadout:
            self.weapon_nr = 1

    def save_weapon_loadout(self):
        self.saved_weapon_loadout = self.weapon_loadout

    def hurt(self, damage, enemy):
        EFFECTS.update((255, 0, 0))
        self.hp -= damage
        if self.hp <= 0:
            last_chance_hp = random.randint(1, 10)
            if self.hp + damage > last_chance_hp:
                self.hp = last_chance_hp
            else:
                for channel_id in range(8):
                    pygame.mixer.Channel(channel_id).fadeout(150)
                LEVEL.restart(enemy)

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def handle_movement(self):
        # Checks for movement (WASD)
        keys_pressed = pygame.key.get_pressed()
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        old_pos = (self.x, self.y)

        # Vector based movement, bc otherwise player could move faster diagonally
        if keys_pressed[K_w] or keys_pressed[K_a] or keys_pressed[K_s] or keys_pressed[K_d]:
            movement_x = 0
            movement_y = 0
            if keys_pressed[K_w]:
                movement_x += self.dir_x
                movement_y += self.dir_y

            if keys_pressed[K_a]:
                movement_x += self.dir_y
                movement_y += -self.dir_x

            if keys_pressed[K_s]:
                movement_x += -self.dir_x
                movement_y += -self.dir_y

            if keys_pressed[K_d]:
                movement_x += -self.dir_y
                movement_y += self.dir_x

            movement_vector = numpy.asarray([[movement_x, movement_y]])  # Needed for normalize() function
            if abs(movement_vector[0][0]) + abs(movement_vector[0][1]) > 0.1:
                normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list

                PLAYER.move(normalized_vector[0] * Player.speed,
                            normalized_vector[1] * Player.speed)
        self.total_movement = sqrt(squared_dist(old_pos, (self.x, self.y)))

    def move(self, x_move, y_move):
        def one_point_collision(y, x):
            if int(x - x_move) == x - x_move:
                return True, False
            if int(y - y_move) == y - y_move:
                return False, True

            x_offset = x - int(x)
            y_offset = y - int(y)

            # Distance to closest round(x/y)
            delta_x = abs(round(x_offset) - x_offset)
            delta_y = abs(round(y_offset) - y_offset)
            if delta_x < delta_y:
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
            if up_right:
                x_collision = True
                y_collision = True
            else:
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


class Door:
    type = 'Normal'
    speed = 0.065
    open_ticks = 90

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value

        self.ticks = 0
        self.opened_state = 0  # 1 is fully opened, 0 is fully closed
        self.state = 0

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def play_sound(self, sound):
        volume = (1 - sqrt(squared_dist((PLAYER.x, PLAYER.y), (self.x + 0.5, self.y + 0.5))) / 32) ** 2
        if volume > 0:
            sound.set_volume(volume)
            sound.play()

    def move(self):
        if self.state > 0:
            if self.state == 1:  # Opening
                if self.opened_state == 0:
                    self.play_sound(self.open_sound)
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
                if self.opened_state == 1:
                    self.play_sound(self.close_sound)
                self.opened_state -= Door.speed
                if self.opened_state < 0:
                    self.opened_state = 0
                    self.state = 0


class BossDoor(Door):
    # Boss door stays unlocked until both of the door sides have been visited
    # This makes sure that once you've gone to the other side of the door there's no going back
    # Going through the door also automatically "wakes up" the boss in the level if there is one
    type = 'Boss'

    def __init__(self, map_pos, tile_value):
        super().__init__(map_pos, tile_value)

        self.locked = False
        if TILEMAP[self.y][self.x + 1] <= 0:
            self.door_fronts = [(self.x + 1.5, self.y + 0.5), (self.x - 0.5, self.y + 0.5)]
        else:
            self.door_fronts = [(self.x + 0.5, self.y + 1.5), (self.x + 0.5, self.y - 0.5)]

    def move(self):
        if self.state > 0:
            if self.state == 1 and not self.locked:  # Opening
                if self.opened_state == 0:
                    self.play_sound(self.open_sound)
                    if len(self.door_fronts) == 2:
                        player_pos = (PLAYER.x, PLAYER.y)
                        if squared_dist(player_pos, self.door_fronts[0]) < squared_dist(player_pos, self.door_fronts[1]):
                            del self.door_fronts[0]
                        else:
                            del self.door_fronts[1]
                self.opened_state += Door.speed
                if self.opened_state > 1:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.opened_state = 1
                    self.state += 1

            elif self.state == 2:  # Staying open
                self.ticks += 1
                safe_dist = 0.5 + Player.half_hitbox
                if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                    player_pos = (PLAYER.x, PLAYER.y)
                    if squared_dist(player_pos, self.door_fronts[0]) < 1:
                        # "Spawn boss"
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.locked = True
                        self.state += 1
                        for e in ENEMIES:
                            if e.type == 'Boss':
                                BOSSHEALTHBAR.start_showing(e)
                                e.status = 'default'
                                e.chasing = True
                                break

                    elif self.ticks >= Door.open_ticks:
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            elif self.state == 3:  # Closing
                if self.opened_state == 1:
                    self.play_sound(self.close_sound)
                self.opened_state -= Door.speed
                if self.opened_state < 0:
                    self.opened_state = 0
                    self.state = 0


class WeaponModel:
    switch_ticks = 6
    w = h = 576

    def __init__(self):
        self.sound_channel = pygame.mixer.Channel(1)

        self.shooting = False
        self.switching = 0

        self.ticks = 0
        self.column = 0
        self.draw_y = 0  # y drawing offset

        self.update()

    def shoot(self, weapon):
        def get_shootable_enemies():
            # Moving weapon x and y behind the player so enemies up close will be harder to miss
            weapon_x = PLAYER.x - PLAYER.dir_x / 5
            weapon_y = PLAYER.y - PLAYER.dir_y / 5
            shootable_enemies = []
            for e in ENEMIES:
                if not e.status == 'dead' and e.needs_to_be_drawn:
                    angle = fixed_angle(e.angle_from_player + pi / 2)
                    if e.type == 'Normal':
                        dir_x = cos(angle) / 4
                        dir_y = sin(angle) / 4
                    else:
                        dir_x = cos(angle) / 2
                        dir_y = sin(angle) / 2
                    enemy_left_side = (e.x - dir_x, e.y - dir_y)
                    enemy_right_side = (e.x + dir_x, e.y + dir_y)
                    enemy_center = (e.x, e.y)
                    hittable_amount = 0
                    if can_see((weapon_x, weapon_y), enemy_left_side, PLAYER.viewangle, FOV):
                        hittable_amount += 0.33
                    if can_see((weapon_x, weapon_y), enemy_right_side, PLAYER.viewangle, FOV):
                        hittable_amount += 0.33
                    if can_see((weapon_x, weapon_y), enemy_center, PLAYER.viewangle, FOV):
                        hittable_amount += 0.33
                    if hittable_amount:
                        shootable_enemies.append((e, hittable_amount))
            shootable_enemies.sort(key=lambda x: x[0].dist_squared)  # Sort for closest dist first
            return shootable_enemies

        def bullet_hitscan(shootable_enemies, x_spread, max_range=False):
            for e, hittable_amount in shootable_enemies:
                enemy_center_display_x = e.display_x + x_spread + (e.width / 2)
                x_offset = abs(H_W - enemy_center_display_x)
                hittable_offset = e.width / 2 * hittable_amount
                if hittable_offset > x_offset:  # If bullet more or less on enemy
                    if not max_range or e.dist_squared <= max_range ** 2:
                        pain = self.weapon.pain_chance * e.pain_chance * 100 >= random.randint(0, 100)
                        e.hurt(weapon.damage, pain)
                    break

        # Shooting animation system
        self.ticks += 1
        if self.ticks == int(weapon.fire_delay / weapon.animation_frames):
            self.ticks = 0
            self.column += 1

            if self.column > weapon.animation_frames:  # If finished shot animation
                # If weapon automatic and mouse down
                if weapon.automatic and pygame.mouse.get_pressed()[0]:
                    self.column = 1  # Keep going
                else:
                    self.column = 0  # Ends animation
                    self.shooting = False

            if self.column == weapon.shot_column:
                shootable_enemies = get_shootable_enemies()

                if weapon.type == 'Melee':
                    bullet_hitscan(shootable_enemies, 0, weapon.range)

                elif weapon.type == 'Hitscan':
                    bullet_hitscan(shootable_enemies, random.randint(-weapon.max_x_spread, weapon.max_x_spread))

                elif weapon.type == 'Shotgun':
                    x_spread_difference = (weapon.max_x_spread * 2) / (weapon.shot_bullets - 1)
                    for i in range(weapon.shot_bullets):
                        bullet_hitscan(shootable_enemies, -weapon.max_x_spread + round(i * x_spread_difference))

                self.sound_channel.play(self.weapon.sounds.fire)

    def switch_weapons(self):
        self.ticks += 1
        if self.ticks == WeaponModel.switch_ticks / 2:
            PLAYER.weapon_nr = self.switching  # Switches weapon model when halfway through
            self.sound_channel.stop()

        if self.ticks <= WeaponModel.switch_ticks / 2:
            self.draw_y += 40
        elif self.ticks <= WeaponModel.switch_ticks:
            self.draw_y -= 40
        else:
            self.ticks = 0
            self.switching = 0

    def update(self):
        self.weapon = WEAPONS[PLAYER.weapon_nr]

        if self.weapon.sounds.idle:
           if not self.shooting:
                if self.sound_channel.get_sound() == self.weapon.sounds.idle:
                    self.sound_channel.queue(self.weapon.sounds.idle)
                else:
                    self.sound_channel.play(self.weapon.sounds.idle)

        if self.shooting:
            self.shoot(self.weapon)

        elif self.switching:
            self.switch_weapons()

    def draw(self):
        weapon_image = self.weapon.weapon_sheet.subsurface(WeaponModel.w * self.column, 0, WeaponModel.w, WeaponModel.h)
        DISPLAY.blit(weapon_image, ((D_W - WeaponModel.w) / 2, D_H - WeaponModel.h + self.draw_y))


class Effects:
    def __init__(self):
        self.colour = None
        self.alpha = 0

    def update(self, colour):
        self.colour = colour
        self.alpha = 128

    def draw(self):
        if self.alpha:
            effect = pygame.Surface((D_W, D_H))
            effect.set_alpha(self.alpha)
            effect.fill(self.colour)
            DISPLAY.blit(effect, (0, 0))
            self.alpha -= 16


class Hud:
    safezone_w = 5
    safezone_h = 5
    font_h = 28

    def draw(self):
        def render_text(text, colour, background=None):
            return GAME_FONT.render(text, False, colour, background)

        # Messages
        y = Hud.safezone_h
        for m in MESSAGES:
            message = render_text(m.text, m.colour)
            message.set_alpha(m.alpha)
            DISPLAY.blit(message, (Hud.safezone_w, y))
            y += Hud.font_h

        # FPS counter
        if SHOW_FPS:
            fps_counter = render_text(str(ceil(CLOCK.get_fps())), (0, 255, 0))
            DISPLAY.blit(fps_counter, (D_W - Hud.safezone_w - fps_counter.get_width(), Hud.safezone_h))

        # Weapon HUD
        WEAPON_MODEL.draw()
        current_weapon = WEAPON_MODEL.weapon

        weapon_name = render_text(str(current_weapon.name), (0, 0, 0))
        DISPLAY.blit(weapon_name, (D_W - weapon_name.get_width() - Hud.safezone_w, D_H - Hud.font_h*2 - Hud.safezone_h))

        # Player hp HUD
        hp_text = render_text('HP:', (0, 0, 0))
        hp_amount = render_text(str(PLAYER.hp), dynamic_colour(PLAYER.hp, Player.max_hp))
        DISPLAY.blit(hp_text, (Hud.safezone_w, D_H - Hud.font_h*2 - Hud.safezone_h))
        DISPLAY.blit(hp_amount, (Hud.safezone_w, D_H - Hud.font_h - Hud.safezone_h))

        # Loadout HUD
        x = D_W - Hud.safezone_w
        for w in reversed(WEAPONS):
            if w:
                weapon_nr = WEAPONS.index(w)
                if w == WEAPON_MODEL.weapon:  # If equipped
                    colour = (0, 255, 0)
                elif weapon_nr in PLAYER.weapon_loadout:  # If picked up
                    colour = (0, 128, 0)
                else:  # If not picked up
                    colour = (0, 32, 0)
                number = render_text(str(weapon_nr), colour)
                x -= number.get_width()
                DISPLAY.blit(number, (x, D_H - Hud.font_h - Hud.safezone_h))
                x -= 10

        BOSSHEALTHBAR.draw()
        EFFECTS.draw()


class Message:
    display_ticks = 150  # How many ticks message stays on screen
    fade_speed = 5  # Rate at which text alpha decreases after display_ticks has gone down to 0
    max_amount = 10  # Max amount of messages that can be on screen

    def __init__(self, text, colour=(255, 255, 255)):
        self.text = text
        self.colour = colour
        self.ticks = Message.display_ticks
        self.alpha = 255
        if len(MESSAGES) > Message.max_amount:
            del MESSAGES[0]

    def update(self):
        if self.ticks == 0:
            self.alpha -= Message.fade_speed
            if self.alpha <= 0:
                MESSAGES.remove(self)
        else:
            self.ticks -= 1


class CameraPlane:
    len = 1

    def __init__(self, rays_amount, fov):
        # Creates a list of rayangle offsets which will be added to player's viewangle to send rays every frame
        # Bc these angle offsets do not change during the game, they are calculated before the game loop starts
        #
        # These offsets are calculated,
        # so that later each casted ray will be equal distance away from other rays on the theoretical camera plane
        # Else the player will see things with a weird fisheye effect
        #
        # Note that in 2D rendering, camera plane is actually a single line, rather than a plane
        # Also fov has to be < pi (and not <= pi) for it to work properly

        self.rayangle_offsets = []

        camera_plane_start = -CameraPlane.len / 2
        camera_plane_step = CameraPlane.len / rays_amount

        self.dist = (CameraPlane.len / 2) / tan(fov / 2)
        for i in range(rays_amount):
            camera_plane_pos = camera_plane_start + i * camera_plane_step

            angle = atan2(camera_plane_pos, self.dist)
            self.rayangle_offsets.append(angle)


class Drawable:
    def adjust_image_height(self):
        # Depending on self.height, (it being the unoptimized image drawing height) this system will crop out
        # as many pixel rows from top and bottom from the unscaled image as possible,
        # while ensuring that the player will not notice a difference, when the image is drawn later
        #
        # It will then also adjust drawing height accordingly
        #
        # Cropping is done before scaling to ensure that the program is not going to be scaling images to enormous sizes

        percentage = D_H / self.height  # Percentage of image that's going to be seen
        perfect_size = TEXTURE_SIZE * percentage  # What would be the perfect cropping size

        # However actual cropping size needs to be the closest even* number rounding up perfect_size
        # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
        # *number needs to be even bc you can't crop at halfpixel
        cropping_size = ceil(perfect_size / 2) * 2

        # Cropping the image smaller - width stays the same
        rect = pygame.Rect((0, (TEXTURE_SIZE - cropping_size) / 2), (self.image.get_width(), cropping_size))
        self.image = self.image.subsurface(rect)

        # Adjusting image height accordingly
        multiplier = cropping_size / perfect_size
        self.height = int(D_H * multiplier)


class WallColumn(Drawable):
    def __init__(self, perp_dist, texture, texture_column, display_x):
        self.perp_dist = perp_dist  # Needs saving to sort by it later
        self.image = texture.subsurface(texture_column, 0, 1, TEXTURE_SIZE)

        self.height = int(Drawable.constant / self.perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        self.display_x = display_x
        self.display_y = (D_H - self.height) / 2
        self.image = pygame.transform.scale(self.image, (WallColumn.width, self.height))

    def draw(self):
        DISPLAY.blit(self.image, (self.display_x, self.display_y))


class Sprite(Drawable):
    animation_ticks = 5  # Sprite animation frames delay

    def draw(self):
        # Optimized sprite drawing function made for Enemies and Objects

        if self.perp_dist > 0:
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
                        DISPLAY.blit(sprite_column, (column_left_side, self.display_y))

                    except pygame.error:  # If size too big (happens rarely and only if player too close to sprite)
                        break  # End drawing sprite

    def calc_display_xy(self, angle_from_player, y_multiplier=1.0):
        # In order to calculate sprite's correct display x/y position, we need to calculate it's camera plane position
        camera_plane_pos = CAMERA_PLANE.len / 2 + tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE.dist

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H - self.height * y_multiplier) / 2


class Object(Sprite):
    def __init__(self, map_pos, tilevalue):
        self.x = map_pos[0] + 0.5
        self.y = map_pos[1] + 0.5

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        if self.perp_dist > 0:
            self.image = TILE_VALUES_INFO[tilevalue].texture

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            angle_from_player = atan2(delta_y, delta_x)
            self.calc_display_xy(angle_from_player)

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)


class Enemy(Sprite):
    type = 'Normal'
    max_draw_dist = 15  # Enemies farther than 15 units won't be drawn in the frame

    def __init__(self, spritesheet, pos):
        self.x, self.y = pos
        self.home = int(self.x), int(self.y)
        self.angle = 0

        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.column = 0  # Spritesheet column

        self.path = []
        self.target_tile = self.home
        self.status = 'default'  # (default, shooting, hit, dead)
        self.chasing = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.channel = pygame.mixer.Channel(ENEMY_INFO[self.sheet].id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.hp = ENEMY_INFO[self.sheet].hp
        self.speed = ENEMY_INFO[self.sheet].speed
        self.wandering_radius = ENEMY_INFO[self.sheet].wandering_radius
        self.shooting_range = ENEMY_INFO[self.sheet].shooting_range
        self.accuracy = ENEMY_INFO[self.sheet].accuracy
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.memory = ENEMY_INFO[self.sheet].memory
        self.patience = ENEMY_INFO[self.sheet].patience
        self.pain_chance = ENEMY_INFO[self.sheet].pain_chance
        self.shot_columns = ENEMY_INFO[self.sheet].shot_columns

        # Timed events tick variables (frames passed since some action)
        self.anim_ticks = 0
        self.last_saw_ticks = self.memory
        self.stationary_ticks = 0

    def __eq__(self, other):
        return self.home == other.home

    def get_home_room(self):
        # Makes a self.home_room list which contains all the map points in his room

        def get_unvisited(pos):
            # Gets new unvisited points
            pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            for pos_offset in pos_offsets:
                pos_x = pos[0] + pos_offset[0]
                pos_y = pos[1] + pos_offset[1]
                if (pos_x, pos_y) not in visited + unvisited and TILEMAP[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))

        visited = [(self.home[0], self.home[1])]
        unvisited = []
        get_unvisited((self.home[0], self.home[1]))

        while unvisited:  # While there is unscanned/unvisited points
            current = unvisited[0]  # Get new point
            del unvisited[0]  # Delete it from unvisited bc it's about to get visited
            visited.append(current)  # Add point to visited
            get_unvisited(current)  # Scan new points from that location

        self.home_room = []
        for room_point in visited:
            if squared_dist(self.home, room_point) <= self.wandering_radius**2:
                self.home_room.append(room_point)

    def get_row_and_column(self, moved):
        angle = fixed_angle(-self.angle_from_player + self.angle) + pi
        self.column = round(angle / (pi / 4))
        if self.column == 8:
            self.column = 0

        if moved:
            running_rows = (1, 2, 3, 4)
            if self.row not in running_rows:
                self.row = 1

            # Cycle through running animations
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.row += 1
                if self.row not in running_rows:
                    self.row = 1
        else:
            self.row = 0
            self.anim_ticks = 0

    def can_step(self, step_x, step_y):
        if (int(PLAYER.x), int(PLAYER.y)) == (step_x, step_y) and self.shooting_range > 1:
            return False

        for e in ENEMIES:
            if not self == e and not e.status == 'dead':  # Ignore self and dead enemies
                if (int(e.x), int(e.y)) == (step_x, step_y):  # If enemy in way
                    return False
        return True

    def get_nearby_alerted_enemy(self):
        for e in ENEMIES:
            if not self == e and e.chasing and can_see((self.x, self.y), (e.x, e.y)):
                    return e
        return None

    def ready_to_shoot(self):
        return self.dist_squared < self.shooting_range**2 and can_see((self.x, self.y), (PLAYER.x, PLAYER.y))

    def stop_animation(self):
        self.status = 'default'
        self.anim_ticks = 0

    def start_shooting(self):
        self.status = 'shooting'
        self.column = 0
        self.anim_ticks = 0

    def shoot(self):
        # speed_factor ranges between 24 (when player's running) and 32 (when not)
        speed_factor = 24 + (32 - 24) * (1 - PLAYER.total_movement / PLAYER.speed)

        dist_from_player = sqrt(self.dist_squared)

        player_hit = random.randint(0, int(32 / self.accuracy)) < speed_factor - dist_from_player
        if player_hit:
            if dist_from_player < 2:
                damage = random.randint(20, 30)
            elif dist_from_player > 4:
                damage = random.randint(0, 10)
            else:
                damage = random.randint(10, 20)
            PLAYER.hurt(int(damage * self.damage_multiplier), self)

    def hurt(self, damage, pain):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.chasing = False
            self.status = 'dead'
            self.anim_ticks = 0
            self.row = 5
            self.column = 0
            self.play_sound(self.sounds.death)
        elif pain:
            self.status = 'hit'
            self.anim_ticks = 0
            self.row = 5
            self.column = 7

    def strafe(self):
        # Gets new path to a random empty neighbour tile (if possible)
        available_tiles = []
        pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for pos_offset in pos_offsets:
            tile_x = int(self.x) + pos_offset[0]
            tile_y = int(self.y) + pos_offset[1]
            if TILEMAP[tile_y][tile_x] <= 0:  # If tile steppable
                available_tiles.append((tile_x, tile_y))

        if available_tiles:
            self.path = pathfinding.pathfind((self.x, self.y) ,random.choice(available_tiles))
        else:
            self.path = []

    def handle_doors_underneath(self):
        # If door underneath enemy, create a door obj if it isn't there already and start opening it immediately
        tile_value = TILEMAP[int(self.y)][int(self.x)]
        if TILE_VALUES_INFO[tile_value].type == 'Door':
            for d in DOORS:
                if (d.x, d.y) == (int(self.x), int(self.y)):
                    d.state = 1
                    break
            else:
                d = Door((int(self.x), int(self.y)), tile_value)
                d.state = 1
                DOORS.append(d)

    def play_sound(self, sound, adjust_volume=True):
        # Plays a required sound
        # If enemy is far from enemy sound will be quieter
        volume = 1
        if adjust_volume:
            volume -= sqrt(self.dist_squared) / 24
        if volume > 0:
            sound.set_volume(volume)
            self.channel.play(sound)

    def update(self):
        self.handle_doors_underneath()

        moved = False
        saw_player = False

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2

        if self.status == 'dead':
            if self.column < 4:
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.column += 1

        elif self.status == 'hit':
            saw_player = True
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks - 2:
                self.stop_animation()

        elif self.status == 'shooting':
            saw_player = True
            self.row = 6

            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0

                self.column += 1
                if self.column in self.shot_columns:
                    self.play_sound(self.sounds.attack)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == 6:
                    self.column = 5

                    if (int(self.x), int(self.y)) == (int(PLAYER.x), int(PLAYER.y)):
                        self.column = 0  # Continues shooting
                    elif random.randint(0, 1) == 0 and self.ready_to_shoot():
                        self.column = 0  # Continues shooting
                    else:
                        self.stop_animation()

        else:
            angle = fixed_angle(self.angle_from_player + pi / 2)
            dir_x = cos(angle) / 4
            dir_y = sin(angle) / 4
            enemy_left_side = (self.x - dir_x, self.y - dir_y)
            enemy_right_side = (self.x + dir_x, self.y + dir_y)
            if can_see((PLAYER.x, PLAYER.y), enemy_left_side) or can_see((PLAYER.x, PLAYER.y), enemy_right_side):
                saw_player = True
                if not self.chasing:
                    self.chasing = True
                    if self.sounds.appearance:
                        self.play_sound(self.sounds.appearance)
                self.target_tile = (int(PLAYER.x), int(PLAYER.y))
            elif self.last_saw_ticks < self.memory:
                self.chasing = True
                self.target_tile = (int(PLAYER.x), int(PLAYER.y))
            else:
                alerted_enemy = self.get_nearby_alerted_enemy()
                if alerted_enemy:
                    self.chasing = True
                    self.target_tile = (int(alerted_enemy.x), int(alerted_enemy.y))
                else:
                    self.chasing = False

            if (self.x - 0.5, self.y - 0.5) == self.target_tile:
                if self.stationary_ticks >= self.patience:
                    if (self.x - 0.5, self.y - 0.5) == self.home:
                        if random.randint(0, 1) == 0:
                            self.target_tile = random.choice(self.home_room)
                        else:
                            self.angle = atan2(-self.delta_y, -self.delta_x)
                            moved = True
                    else:
                        self.target_tile = self.home
                elif self.chasing and self.ready_to_shoot():
                    self.start_shooting()
            else:
                if not self.path:
                    self.path = pathfinding.pathfind((self.x, self.y), self.target_tile)
                if self.path:
                    moved = True
                    step_x, step_y = self.path[0]
                    if not self.can_step(step_x, step_y):
                        if self.chasing and random.randint(0, 1) == 0 and self.ready_to_shoot():
                            self.start_shooting()
                        else:
                            self.strafe()
                    else:
                        step_x += 0.5
                        step_y += 0.5
                        self.angle = atan2(step_y - self.y, step_x - self.x)
                        self.x += cos(self.angle) * self.speed
                        self.y += sin(self.angle) * self.speed

                        if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                            self.x = step_x
                            self.y = step_y
                            self.path = pathfinding.pathfind((self.x, self.y), self.target_tile)

                            if self.chasing and self.ready_to_shoot():
                                self.start_shooting()
                            elif not self.path:
                                self.angle = atan2(-self.delta_y, -self.delta_x)
            if not self.status == 'shooting':
                self.get_row_and_column(moved)

        if moved:
            self.stationary_ticks = 0
        else:
            self.stationary_ticks += 1
            if self.stationary_ticks > self.patience:
                self.stationary_ticks = self.patience
        if saw_player:
            self.last_saw_ticks = 0
        else:
            self.last_saw_ticks += 1
            if self.last_saw_ticks > self.memory:
                self.last_saw_ticks = self.memory

        self.update_for_drawing()

    def update_for_drawing(self):
        self.needs_to_be_drawn = False
        if squared_dist((self.x, self.y), (PLAYER.x, PLAYER.y)) < self.max_draw_dist**2:
            self.needs_to_be_drawn = True
            self.perp_dist = self.delta_x * PLAYER.dir_x + self.delta_y * PLAYER.dir_y
            if self.perp_dist > 0:
                self.image = self.sheet.subsurface(self.column * TEXTURE_SIZE, self.row * TEXTURE_SIZE,
                                                   TEXTURE_SIZE, TEXTURE_SIZE)

                self.height = self.width = int(Drawable.constant / self.perp_dist)
                if self.height > D_H:
                    self.adjust_image_height()

                self.calc_display_xy(self.angle_from_player)


class Boss(Enemy):
    type = 'Boss'
    pain_chance = 0.00

    def __init__(self, spritesheet, pos):
        self.x, self.y = self.home = pos

        self.sheet = spritesheet
        self.row = 0
        self.column = 0

        self.path = []
        self.status = 'sleeping'
        self.chasing = False
        self.seen_player = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.channel = pygame.mixer.Channel(ENEMY_INFO[self.sheet].id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.max_hp = self.hp = ENEMY_INFO[spritesheet].hp
        self.speed = ENEMY_INFO[spritesheet].speed
        self.accuracy = ENEMY_INFO[spritesheet].accuracy
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.shot_columns = ENEMY_INFO[spritesheet].shot_columns

        self.anim_ticks = 0

    def stop_animation(self):
        self.status = 'default'
        self.anim_ticks = 0
        self.row = 0
        self.column = 0

    def can_step(self, step_x, step_y):
        if (int(PLAYER.x), int(PLAYER.y)) == (step_x, step_y):
            return False

        for e in ENEMIES:
            if not self == e and not e.status == 'dead':
                if (int(e.x), int(e.y)) == (step_x, step_y):
                    return False
        return True

    def ready_to_shoot(self):
        return can_see((self.x, self.y), (PLAYER.x, PLAYER.y))

    def hurt(self, damage, pain):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.chasing = False
            self.status = 'dead'
            self.anim_ticks = 0
            self.row = 2
            self.column = 0
            PLAYER.has_key = True
            self.play_sound(self.sounds.death)

    def update(self):
        self.handle_doors_underneath()

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2

        if self.status == 'dead':
            if self.column < 7:
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.column += 1

        elif self.status == 'shooting':
            self.row = 1

            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.column += 1
                if self.column in self.shot_columns:
                    if self.channel.get_sound() != self.sounds.appearance:
                        self.play_sound(self.sounds.attack)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == 8:
                    self.column = 7
                    self.stop_animation()

        elif self.status == 'default':
            if not self.channel.get_busy():
                self.play_sound(self.sounds.step)
            if not self.path:
                self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
            step_x, step_y = self.path[0]
            if not self.can_step(step_x, step_y):
                if random.randint(0, 1) == 0:
                    self.start_shooting()
                else:
                    self.strafe()
            else:
                step_x += 0.5
                step_y += 0.5
                angle = atan2(step_y - self.y, step_x - self.x)
                self.x += cos(angle) * self.speed
                self.y += sin(angle) * self.speed

                if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                    self.x = step_x
                    self.y = step_y
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
                    if not self.seen_player and can_see((self.x, self.y), (PLAYER.x, PLAYER.y)):
                        self.play_sound(self.sounds.appearance, False)
                        self.seen_player = True

                    if self.ready_to_shoot():
                        self.start_shooting()

            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.column += 1
                if self.column == 4:
                    self.column = 0

        self.update_for_drawing()


class BossHealthBar:
    w = 400
    h = 24
    def __init__(self):
        self.visible = False
        self.x = (D_W - BossHealthBar.w) / 2
        self.y = -64

    def start_showing(self, boss):
        self.boss = boss
        self.boss_image = self.boss.sheet.subsurface(0, 0, TEXTURE_SIZE, TEXTURE_SIZE)
        self.visible = True

    def draw(self):
        if self.visible:
            if self.boss.hp == 0:
                self.y -= 8
                if self.y == -64:
                    self.visible = False
            elif self.y < 24:
                self.y += 8

            colour = dynamic_colour(self.boss.hp, self.boss.max_hp)
            health_percentage = self.boss.hp / self.boss.max_hp

            pygame.draw.rect(DISPLAY, (0, 0, 0), (self.x - 4, self.y - 4, BossHealthBar.w + 8, BossHealthBar.h + 8))
            pygame.draw.rect(DISPLAY, colour, (self.x, self.y, BossHealthBar.w * health_percentage, BossHealthBar.h))

            DISPLAY.blit(self.boss_image, (self.x - 32, self.y + BossHealthBar.h / 2 - 32))


class Level:
    def load(self, level_nr):
        self.nr = level_nr
        # Create tilemap
        with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
            global TILEMAP
            TILEMAP = []
            for line in f:
                row = line.replace('\n', '')  # Get rid of newline (\n)
                row = row[1:-1]  # Get rid of '[' and ']'
                row = row.split(',')  # Split line into list
                row = [int(i) for i in row]  # Turn all number strings to an int
                TILEMAP.append(row)

        # Create player
        with open('../levels/{}/player.txt'.format(level_nr), 'r') as f:
            player_pos = f.readline().replace('\n', '').split(',')
            player_pos = [float(i) for i in player_pos]
            player_angle = float(f.readline().replace('\n', ''))
            global PLAYER
            PLAYER.setup(player_pos, player_angle)

        # Background
        with open('../levels/{}/background.txt'.format(level_nr), 'r') as f:
            colour = f.readline().replace('\n', '').split(',')
            colour = [int(i) for i in colour]
            self.ceiling_colour = tuple(colour)
            colour = f.readline().replace('\n', '').split(',')
            colour = [int(i) for i in colour]
            self.floor_colour = tuple(colour)

            self.skytexture = None
            value = int(f.readline().replace('\n', ''))
            if value > 0:
                skytextures = os.listdir('../textures/skies')
                try:
                    self.skytexture = pygame.image.load('../textures/skies/{}'.format(skytextures[value - 1])).convert()
                except pygame.error or IndexError:
                    pass
                else:
                    self.skytexture = pygame.transform.scale(self.skytexture, (D_W * 4, H_H))

        global DOORS
        DOORS = []
        global EFFECTS
        EFFECTS = Effects()
        global WEAPON_MODEL
        WEAPON_MODEL = WeaponModel()
        global BOSSHEALTHBAR
        BOSSHEALTHBAR = BossHealthBar()

        # Enemies
        global ENEMIES
        ENEMIES = []
        for row in range(len(TILEMAP)):
            for column in range(len(TILEMAP[row])):
                tile = TILE_VALUES_INFO[TILEMAP[row][column]]
                if tile.type == 'Enemy':
                    spritesheet = TILE_VALUES_INFO[TILEMAP[row][column]].texture
                    pos = (column + 0.5, row + 0.5)
                    if tile.desc == 'Normal':
                        ENEMIES.append(Enemy(spritesheet, pos))
                    elif tile.desc == 'Boss':
                        ENEMIES.append(Boss(spritesheet, pos))
                    TILEMAP[row][column] = 0  # Clears tile
        # Process some stuff after enemies have been cleared from tilemap
        for e in ENEMIES:
            if e.type == 'Normal':
                e.get_home_room()

        # Run pathfinding setup function
        pathfinding.setup(TILEMAP, TILE_VALUES_INFO)

    def start(self, level_nr):
        global TIME
        TIME = 0

        self.load(level_nr)
        update_gameobjects()
        game_loop()

    def restart(self, enemy=None):
        send_rays()
        draw_frame()
        pygame.display.flip()
        CLOCK.tick(30)

        # Turn towards enemy
        overlay_alpha = 0
        if enemy:
            turn_speed = 0.05
            angle_to_enemy = atan2(enemy.delta_y, enemy.delta_x)
            difference = (angle_to_enemy + pi) - (PLAYER.viewangle + pi)
            if difference < 0:
                difference += 2 * pi
            if difference < pi:
                turn_radians = turn_speed
            else:
                turn_radians = -turn_speed

            while abs(PLAYER.viewangle - angle_to_enemy) > turn_speed:
                pygame.mouse.get_rel()
                pygame.event.clear()

                PLAYER.viewangle = fixed_angle(PLAYER.viewangle + turn_radians)
                PLAYER.dir_x = cos(PLAYER.viewangle)
                PLAYER.dir_y = sin(PLAYER.viewangle)

                for e in ENEMIES:
                    e.update_for_drawing()

                send_rays()
                draw_frame()

                if overlay_alpha != 128:
                    overlay_alpha += 8
                black_overlay = pygame.Surface((D_W, D_H))
                black_overlay.set_alpha(overlay_alpha)
                black_overlay.fill((0, 0, 0))
                DISPLAY.blit(black_overlay, (0, 0))

                pygame.display.flip()
                CLOCK.tick(30)

        global QUIT
        text_alpha = 0
        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            send_rays()
            draw_frame()

            text_alpha -= 15
            if text_alpha < -255:
                text_alpha = 255

            if overlay_alpha != 128:
                overlay_alpha += 8
            black_overlay = pygame.Surface((D_W, D_H))
            black_overlay.set_alpha(overlay_alpha)
            black_overlay.fill((0, 0, 0))
            DISPLAY.blit(black_overlay, (0, 0))

            you_died = GAME_FONT.render('YOU DIED', False, (255, 255, 255))
            you_died.set_alpha(abs(text_alpha))
            DISPLAY.blit(you_died, ((D_W - you_died.get_width()) / 2, (D_H - you_died.get_height()) / 2))

            pygame.display.flip()
            CLOCK.tick(30)

        pygame.mouse.get_rel()
        pygame.event.clear()
        self.start(self.nr)

    def finish(self):
        PLAYER.save_weapon_loadout()

        global QUIT
        seconds = int(TIME / 30)  # Rounds time spent down, 45.8 seconds will display 45
        minutes = 0
        while seconds >= 60:
            minutes += 1
            seconds -= 60
        dead = 0
        for e in ENEMIES:
            if e.status == 'dead':
                dead += 1
        overlay_alpha = 0
        text_alpha = 0
        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            send_rays()
            draw_frame()

            text_alpha -= 15
            if text_alpha < -255:
                text_alpha = 255

            if overlay_alpha != 128:
                overlay_alpha += 8
            black_overlay = pygame.Surface((D_W, D_H))
            black_overlay.set_alpha(overlay_alpha)
            black_overlay.fill((0, 0, 0))
            DISPLAY.blit(black_overlay, (0, 0))

            level_finished = GAME_FONT.render('LEVEL FINISHED', False, (255, 255, 255))
            time_spent = GAME_FONT.render('TIME: {}m {}s'.format(minutes, seconds), False, (255, 255, 255))
            kills = GAME_FONT.render('KILLS: {}/{}'.format(len(ENEMIES), dead), False, (255, 255, 255))
            DISPLAY.blit(level_finished, ((D_W - level_finished.get_width()) / 2, 300))
            DISPLAY.blit(time_spent, ((D_W - time_spent.get_width()) / 2, 400))
            DISPLAY.blit(kills, ((D_W - kills.get_width()) / 2, 500))

            pygame.display.flip()
            CLOCK.tick(30)

        self.start(self.nr + 1)


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def fixed_angle(angle):
    # Makes sure all angles stay between -pi and pi

    while angle > pi:  # 3.14+
        angle -= 2 * pi
    while angle < -pi:  # 3.14-
        angle += 2 * pi
    return angle


def can_see(from_, to, viewangle=0.0, fov=0.0):
    # Universal function for checking if it's possible to see one point from another in tilemap
    # Returns True if end point visible, False if not visible

    start_x, start_y = from_
    end_x, end_y = to
    angle_to_end = atan2(end_y - start_y, end_x - start_x)

    if viewangle and fov:  # If viewangle and fov given
        if abs(angle_to_end - viewangle) > fov / 2:  # If end position outside viewangle
            return False

    # Check if there is something between end and start point
    ray_x, ray_y = simple_raycast(angle_to_end, from_)
    return squared_dist(from_, (ray_x, ray_y)) > squared_dist(from_, to)  # True if interception farther than end point


def dynamic_colour(current, maximum):
    ratio = current / maximum  # 1 is completely green, 0 completely red
    if ratio < 0.5:
        r = 255
        g = int(ratio * 2 * 255)
    else:
        ratio = 1 - ratio
        g = 255
        r = int(ratio * 2 * 255)
    b = 0
    return r, g, b


def send_rays():
    global WALLS
    WALLS = []
    global OBJECTS
    OBJECTS = []
    for c, rayangle_offset in enumerate(CAMERA_PLANE.rayangle_offsets):
        # Get the rayangle that's going to be raycasted
        rayangle = fixed_angle(PLAYER.viewangle + rayangle_offset)

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
                texture = Door.side_texture
                break
        else:
            texture = TILE_VALUES_INFO[tile_value].texture

        # Create Wall object
        WALLS.append(WallColumn(perp_dist, texture, column, c * WallColumn.width))


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
        # to determine the interception type and to calculate other variables depending on that interception type
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
        if tile_value != 0:
            tile_type = TILE_VALUES_INFO[tile_value].type

            if tile_type == 'Object':
                for obj in OBJECTS:
                    if (obj.x - 0.5, obj.y - 0.5) == (map_x, map_y):
                        break
                else:
                    OBJECTS.append(Object((map_x, map_y), tile_value))
                continue

            if tile_type == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                # Add door to DOORS if it's not in it already
                for d in DOORS:
                    if (d.x, d.y) == (map_x, map_y):
                        door = d
                        break
                else:
                    if TILE_VALUES_INFO[tile_value].desc != 'Boss':  # If not Boss door
                        door = Door((map_x, map_y), tile_value)
                        DOORS.append(door)
                    else:
                        door = BossDoor((map_x, map_y), tile_value)
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

            else:  # If wall
                if side == 0:
                    offset = abs(ray_y - int(ray_y) - (1 - A))
                else:
                    offset = abs(ray_x - int(ray_x) - B)
                column = int(TEXTURE_SIZE * offset)

            if side == 0:
                column += TEXTURE_SIZE  # Makes block sides different

            return tile_value, ray_x, ray_y, column


def simple_raycast(rayangle, start_pos, side_needed=False):
    # Used to only get the ray interception point without creating objects that are in the way

    if abs(rayangle) > pi / 2:
        A = 0
    else:
        A = 1
    if rayangle < 0:
        B = 0
    else:
        B = 1

    ray_x, ray_y = start_pos
    tan_rayangle = tan(rayangle)

    while True:
        x_offset = ray_x - int(ray_x)
        if x_offset == A:
            x_offset = 1

        y_offset = ray_y - int(ray_y)
        if y_offset == B:
            y_offset = 1

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
        if tile_value != 0:
            tile_type = TILE_VALUES_INFO[tile_value].type

            if tile_type == 'Object':
                continue

            if tile_type == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                for d in DOORS:
                    if (d.x, d.y) == (map_x, map_y):
                        door = d
                        break
                else:
                    # Create a closed door
                    door = Door((map_x, map_y), tile_value)

                if side == 0:  # If vertical ( | )
                    interception_y = (-0.5 + A) * tan_rayangle
                    offset = ray_y + interception_y - int(ray_y + interception_y)
                    if int(ray_y - y_offset) == int(ray_y + interception_y) and offset > door.opened_state:
                        ray_x += (-0.5 + A)
                        ray_y += interception_y
                    else:
                        continue

                else:  # If horizontal ( -- )
                    interception_x = (-0.5 + B) / tan_rayangle
                    offset = ray_x + interception_x - int(ray_x + interception_x)
                    if int(ray_x - x_offset) == int(ray_x + interception_x) and offset > door.opened_state:
                        ray_x += interception_x
                        ray_y += (-0.5 + B)
                    else:
                        continue
            if not side_needed:
                return ray_x, ray_y
            else:
                return ray_x, ray_y, side


def events():
    global PAUSED
    global SHOW_FPS
    global QUIT

    if PAUSED:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = False
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS
                elif event.key == K_RETURN:
                    QUIT = True
        pygame.mouse.get_rel()

    else:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = True
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS

                if event.key == K_e:
                    x = int(PLAYER.x + PLAYER.dir_x)
                    y = int(PLAYER.y + PLAYER.dir_y)
                    tile_value = TILEMAP[y][x]
                    tile_type = TILE_VALUES_INFO[tile_value].type
                    tile_desc = TILE_VALUES_INFO[tile_value].desc
                    if tile_type == 'Door' and tile_desc != 'Static':
                        if PLAYER.has_key or tile_desc == 'Dynamic' or tile_desc == 'Boss':
                            for d in DOORS:
                                # If found the right door and it's not in motion already
                                if x == d.x and y == d.y:
                                    d.state = 1
                                    break
                    elif tile_type == 'Wall' and tile_desc == 'End-trigger':
                        TILEMAP[y][x] += 1  # Change trigger block texture
                        LEVEL.finish()

                elif not WEAPON_MODEL.shooting:
                    key = pygame.key.name(event.key)
                    numbers = (str(x) for x in range(1, 10))
                    if key in numbers:
                        key = int(key)
                        if key in PLAYER.weapon_loadout and key != PLAYER.weapon_nr:
                            WEAPON_MODEL.switching = key

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not WEAPON_MODEL.switching:
                        WEAPON_MODEL.shooting = True


def update_gameobjects():
    for c, d in enumerate(DOORS):
        d.move()
        if d.type == 'Normal' and d.state == 0:  # Only deletes normal doors that are closed
            del DOORS[c]
    for e in ENEMIES:
        e.update()
    for m in MESSAGES:
        m.update()
    WEAPON_MODEL.update()
    handle_objects_under_player()


def handle_objects_under_player():
    # Checking if player is standing on an object bc raycast() will miss objects player is standing on
    # Also picks up objects if they can be picked up
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:
        OBJECTS.append(Object((int(PLAYER.x), int(PLAYER.y)), tile_value))
        if TILE_VALUES_INFO[tile_value].desc == 'Dynamic':
            colour = None
            type = 0  # 0 = item, 1 = weapon
            # First handle all now-weapon pickups
            if tile_value == -5:
                PLAYER.has_key = True
                colour = (255, 255, 0)
            elif tile_value == -6:
                if PLAYER.hp < PLAYER.max_hp:
                    PLAYER.hp += 10
                    if PLAYER.hp > PLAYER.max_hp:
                        PLAYER.hp = PLAYER.max_hp
                    colour = (0, 255, 0)
            elif tile_value == -7:
                if PLAYER.hp < PLAYER.max_hp:
                    PLAYER.hp += 25
                    if PLAYER.hp > PLAYER.max_hp:
                        PLAYER.hp = PLAYER.max_hp
                    colour = (0, 255, 0)
            # Then handle weapon pickups
            if not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
                if tile_value == -1:
                    if not 5 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(5)
                        WEAPON_MODEL.switching = 5
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -2:
                    if not 4 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(4)
                        WEAPON_MODEL.switching = 4
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -3:
                    if not 3 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(3)
                        WEAPON_MODEL.switching = 3
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -4:
                    if not 2 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(2)
                        WEAPON_MODEL.switching = 2
                    colour = (0, 0, 255)
                    type = 1
            if colour:
                EFFECTS.update(colour)
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0
                if type == 0:
                    ITEM_PICKUP_SOUND.play()
                else:
                    WEAPON_PICKUP_SOUND.play()


def draw_frame():
    if LEVEL.skytexture:
        # x_offset is a value ranging from 0 to 1
        x_offset = (PLAYER.viewangle + pi) / (2 * pi)
        x = x_offset * LEVEL.skytexture.get_width()

        if x_offset <= 0.75:
            # Sky texture can be drawn as one image
            sky = LEVEL.skytexture.subsurface(x, 0, D_W, H_H)
            DISPLAY.blit(sky, (0, 0))
        else:
            # Sky texture needs to be drawn as two separate parts
            sky_left = LEVEL.skytexture.subsurface(x, 0, LEVEL.skytexture.get_width() - x, H_H)
            sky_right = LEVEL.skytexture.subsurface(0, 0, D_W - sky_left.get_width(), H_H)
            DISPLAY.blit(sky_left, (0, 0))
            DISPLAY.blit(sky_right, (sky_left.get_width(), 0))
    else:
        pygame.draw.rect(DISPLAY, LEVEL.ceiling_colour, ((0, 0), (D_W, H_H)))  # Ceiling
    pygame.draw.rect(DISPLAY, LEVEL.floor_colour, ((0, H_H), (D_W, H_H)))  # Floor

    # Sorting objects by perp_dist so those further away are drawn first
    to_draw = WALLS + OBJECTS
    for e in ENEMIES:
        if e.needs_to_be_drawn:
            to_draw.append(e)
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)
    for obj in to_draw:
        obj.draw()


def update_sound_channels():
    for channel_id in range(8):
        if PAUSED:
            pygame.mixer.Channel(channel_id).pause()
        else:
            pygame.mixer.Channel(channel_id).unpause()


def draw_pause_overlay():
    pause_overlay = pygame.Surface((D_W, D_H))
    pause_overlay.set_alpha(128)
    pause_overlay.fill((0, 0, 0))
    DISPLAY.blit(pause_overlay, (0, 0))
    paused = GAME_FONT.render('PAUSED', False, (255, 255, 255))
    DISPLAY.blit(paused, ((D_W - paused.get_width()) / 2, (D_H - paused.get_height()) / 2))


def game_loop():
    global TIME
    while not QUIT:
        events()
        if not PAUSED:
            PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
            PLAYER.handle_movement()
            update_gameobjects()
            TIME += 1

        send_rays()
        draw_frame()
        HUD.draw()

        if PAUSED:
            draw_pause_overlay()

        pygame.display.flip()
        CLOCK.tick(30)


if __name__ == '__main__':
    import os

    from math import *
    import random

    import numpy
    from sklearn.preprocessing import normalize

    import pygame
    from pygame.locals import *

    from game.settings import *
    import game.graphics as graphics
    import game.sounds as sounds
    import game.enemies as enemies
    import game.weapons as weapons
    import game.pathfinding as pathfinding

    # Make class constants
    Drawable.constant = 0.65 * D_H
    WallColumn.width = int(D_W / RAYS_AMOUNT)

    # Pygame stuff
    pygame.mixer.pre_init(11025, -16, 1, 256)
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.event.set_allowed([KEYDOWN, MOUSEBUTTONDOWN])

    CAMERA_PLANE = CameraPlane(RAYS_AMOUNT, FOV)
    GAME_FONT = pygame.font.Font('../font/LCD_Solid.ttf', 32)
    MESSAGES = []
    HUD = Hud()

    Door.side_texture = graphics.get_door_side_texture()
    ENEMY_INFO = enemies.get_enemy_info()
    TILE_VALUES_INFO = graphics.get_tile_values_info(TEXTURE_SIZE, ENEMY_INFO)
    WEAPONS = weapons.get()

    # Sounds
    Door.open_sound,\
    Door.close_sound,\
    ITEM_PICKUP_SOUND,\
    WEAPON_PICKUP_SOUND = sounds.get()

    QUIT = False
    PAUSED = False
    SHOW_FPS = False

    PLAYER = Player()
    LEVEL = Level()
    LEVEL.start(1)
    pygame.quit()
