class Door:
    def __init__(self, pos):
        self.pos = pos
        self.neighbours = []


def get_neighbour_doors(pos):
    # Returns a list of doors that can be reached from given location
    def get_unvisited(pos):
        all_points = visited + unvisited
        for x in range(-1, 2):  # -1, 0, 1
            for y in range(-1, 2):  # -1, 0, 1
                pos_x, pos_y = (pos[0] + x, pos[1] + y)
                if (pos_x, pos_y) not in all_points:
                    if TILEMAP[pos_y][pos_x] <= 0:
                        unvisited.append((pos_x, pos_y))
                    elif TILE_VALUES_INFO[TILEMAP[pos_y][pos_x]][0] == ('Door', 'Dynamic'):
                        visited.append((pos_x, pos_y))
                        doors_found.append((pos_x, pos_y))

    doors_found = []

    visited = [pos]
    unvisited = []
    get_unvisited(pos)

    while unvisited:  # While there is unscanned points
        current = unvisited[0]  # Get new point
        del unvisited[0]  # Delete it from unvisited bc it's about to get visited
        visited.append(current)  # Add point to visited
        get_unvisited(current)  # Scan new points from that location

    return sorted(doors_found)


def setup(tilemap, tile_values_info):
    # Pathfinding setup

    # Creating 3 global variables for itself to use later
    global TILEMAP
    global TILE_VALUES_INFO
    global DOORS
    TILEMAP = tilemap
    TILE_VALUES_INFO = tile_values_info

    # Scanning through tilemap and getting all the doors
    DOORS = []
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            if TILE_VALUES_INFO[TILEMAP[row][column]][0] == ('Door', 'Dynamic'):
                DOORS.append(Door((column, row)))

    # Getting all door neighbours
    for parent_door in DOORS:
        neighbours = get_neighbour_doors(parent_door.pos)
        for child_door in DOORS:
            if child_door.pos in neighbours:
                parent_door.neighbours.append(child_door)


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def a_star(start, end):
    # Simplified version of A* search algorithm

    class Point:
        # Class to store point distances
        def __init__(self, pos):
            self.dist = squared_dist(pos, end)

    def get_path():
        # Trace back the visited tiles and get the path
        path = [end]
        while path[-1] != start:
            # Get neighbour points
            while True:
                point_x, point_y = path[-1]
                neighbours = []
                for x in range(-1, 2):  # -1, 0, 1
                    for y in range(-1, 2):  # -1, 0, 1
                        pos = (point_x + x, point_y + y)
                        if pos in visited and pos not in path:
                            neighbours.append(pos)
                if not neighbours:
                    # Delete that point from path and visited and find new neighbour points
                    del path[-1]
                    del visited[visited.index((point_x, point_y))]
                    continue
                else:
                    break

            # Find the closest neighbour to start
            best_dist = 9999
            for pos in neighbours:
                neighbour_dist = squared_dist(pos, start)
                if neighbour_dist < best_dist:
                    best_dist = neighbour_dist
                    winner_point = pos

            path.append(winner_point)

        del path[-1]
        return path[::-1]

    def get_unvisited(pos):
        all_points = visited + unvisited
        for x in range(-1, 2):  # -1, 0, 1
            for y in range(-1, 2):  # -1, 0, 1
                pos_x, pos_y = (pos[0] + x, pos[1] + y)
                if (pos_x, pos_y) not in all_points and TILEMAP[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))
                    points.append(Point((pos_x, pos_y)))

    end_value = TILEMAP[end[1]][end[0]]  # Remember end value
    TILEMAP[end[1]][end[0]] = 0  # Modify tilemap in case end location is a door

    points = []  # List storing Point class objects

    visited = [start]  # Points that have been visited
    unvisited = []  # Unvisited points that can be visited next step
    current = start  # Stores current point pos

    while visited[-1] != end:  # Quits if end position is in visited
        get_unvisited(current)  # Get new unvisited options
        if not unvisited:  # If path cannot be created
            return []  # Return emtpy list

        # Find the best point's index
        best_dist = 9999
        for index, point in enumerate(points):
            if point.dist < best_dist:
                best_dist = point.dist
                winner_index = index

        current = unvisited[winner_index]  # Update current point
        del points[winner_index]  # Remove the same pos Point obj from points
        del unvisited[winner_index]  # Remove that point from unvisited
        visited.append(current)  # Add current to visited

    TILEMAP[end[1]][end[0]] = end_value  # Change back tilemap
    return get_path()


def pathfind(start, end):
    # Main pathfinding system

    # Turn start and end positons to ints
    start = (int(start[0]), int(start[1]))
    end = (int(end[0]), int(end[1]))

    start_doors = get_neighbour_doors(start)
    end_doors = get_neighbour_doors(end)
    if start_doors == end_doors:
        return a_star(start, end)
    if end in start_doors or start in end_doors:
        return a_star(start, end)

    # If start and end in different rooms
    # Get best starting door
    best_dist = 9999
    for start_door in start_doors:
        door_dist = squared_dist(start_door, end)
        if door_dist < best_dist:
            best_dist = door_dist
            winner_door = start_door  # Winner door pos
    for door in DOORS:
        if door.pos == winner_door:  # If found the door
            winner_door = door  # Winner door object
            break

    # Find doors path
    doors_path = [winner_door]
    visited_doors = []

    while doors_path[-1].pos not in end_doors:
        # Find best neighbour door
        while True:
            door = doors_path[-1]
            neighbours = []
            for n in door.neighbours:
                if n not in visited_doors:
                    neighbours.append(n)
            if not neighbours:
                del doors_path[-1]
                visited_doors.append(door)  # Mark door as visited so it will not be visited again
                continue
            else:
                break

        # Find the closest neighbour to end
        best_dist = 9999
        for n in neighbours:
            neighbour_dist = squared_dist(n.pos, end)
            if neighbour_dist < best_dist:
                best_dist = neighbour_dist
                winner_neighbour = n

        doors_path.append(winner_neighbour)
        visited_doors.append(winner_neighbour)

    # Put together final path
    path = []
    old = start
    for point in doors_path:
        path += a_star(old, point.pos)
        old = point.pos
    path += a_star(old, end)

    return path


if __name__ == '__main__':
    import raycasting.game.graphics as graphics
    import sys
    import pygame
    from pygame.locals import *

    pygame.init()
    DISPLAY = pygame.display.set_mode((1024, 1024))
    CLOCK = pygame.time.Clock()

    enemy_info = graphics.get_enemy_info(sys, pygame)
    tile_values_info = graphics.get_tile_values_info(sys, pygame, 64, enemy_info)
    tilemap = []
    with open('../levels/2/tilemap.txt', 'r') as f:
        row = f.readline().replace('\n', '').split(',')
        row = tuple(int(float(i)) for i in row)
        start = row[0:2]
        # Skip the level colour lines
        next(f)
        next(f)
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            tilemap.append(row)

    setup(tilemap, tile_values_info)

    end_x, end_y = 0, 0
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        DISPLAY.fill((255, 255, 255))

        # Draw the tilemap
        for row in range(64):
            for column in range(64):
                tile_value = TILEMAP[row][column]
                if tile_value != 0:
                    texture = TILE_VALUES_INFO[tile_value][1]
                    texture = texture.subsurface(0, 0, 64, 64)
                    texture = pygame.transform.scale(texture, (16, 16))
                    DISPLAY.blit(texture, (column * 16, row * 16))

        end_x += 1
        if end_x > 63:
            end_x = 0
            end_y += 1
            if end_y > 63:
                end_y = 0
        pygame.draw.rect(DISPLAY, (0, 255, 0), (end_x*16, end_y*16, 16, 16))
        if TILEMAP[end_y][end_x] <= 0:
            # Draw path in red
            path = pathfind(start, (end_x, end_y))
            old_x, old_y = start
            for point_x, point_y in path:
                pygame.draw.line(DISPLAY, (255, 0, 0),
                                 (  (old_x+.5) * 16,   (old_y+.5) * 16),
                                 ((point_x+.5) * 16, (point_y+.5) * 16))
                old_x, old_y = point_x, point_y

        pygame.display.flip()
        CLOCK.tick()

    pygame.quit()
