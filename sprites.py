import math
import random

from itertools import permutations
import heapq

import pygame
import os
import config

class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]

class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        unvisited_nodes = set(range(1, len(coin_distance[0])))
        # print(unvisited_nodes)
        # print(coin_distance)
        return_path = [0]
        current_node = 0
        while len(unvisited_nodes) != 0:
            cost_to_next = float('inf')
            next_node = -1
            for node in unvisited_nodes:
                if coin_distance[current_node][node] < cost_to_next:
                    next_node = node
                    cost_to_next = coin_distance[current_node][node]
            unvisited_nodes.remove(next_node)
            return_path.append(next_node)
            current_node = next_node
        return_path.append(0)
        return return_path

def calculate_path_cost(path: list, coin_distance):
    cost = 0
    index = 0
    while index < len(path) - 1:
        cost += coin_distance[path[index]][path[index + 1]]
        index += 1
    return cost

class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        # print(list(range(1, len(coin_distance[0]))))
        all_paths = list(permutations(range(1, len(coin_distance[0]))))
        optimal_path = [0, *(all_paths[0]), 0]
        optimal_cost = calculate_path_cost(optimal_path, coin_distance)

        for path in all_paths:
            path_cost = calculate_path_cost([0, *path, 0], coin_distance)
            if path_cost < optimal_cost:
                optimal_cost = path_cost
                optimal_path = [0, *path, 0]

        return optimal_path


class PqNode(object):
    def __init__(self, cost: int, path: list):
        self.cost = cost
        self.path = path 

    def __repr__(self):
        return f'Node value: {self.cost}, {self.path}'

    def __lt__(self, other):
        if self.cost == other.cost and len(self.path) == len(other.path):
            return self.path[-1] < other.path[-1]
        elif self.cost == other.cost:
            return len(self.path) > len(other.path)
        else:
            return self.cost < other.cost

class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        queue = []
        heapq.heappush(queue, PqNode(0, [0]))
        bnb_path = [0]
        while len(queue) > 0:
            cur_path = heapq.heappop(queue).path
            if len(cur_path) < len(coin_distance[0]):
                # the if condition will assure that there is no zero
                index = 0
                while index < len(coin_distance[0]):
                    if index not in cur_path:
                        new_path = [*cur_path, index]
                        heapq.heappush(queue, PqNode(calculate_path_cost(new_path, coin_distance), new_path))
                    index += 1
            elif len(cur_path) == len(coin_distance[0]):
                # looking for zero to terminate
                new_path = [*cur_path, 0]
                heapq.heappush(queue, PqNode(calculate_path_cost(new_path, coin_distance), new_path))
            else:
                # found the optimal path
                bnb_path = cur_path
                break
        return bnb_path

def modified_mst_Prim_cost(graph: list, cur_path: list):
    # print(f'Calculating MST cost for path: {cur_path}')
    nodes = list(range(0, len(graph[0])))
    for node in cur_path:
        if node != cur_path[0] and node != cur_path[-1]:
            nodes.remove(node)
    # print(f'Including nodes: {nodes}')
    
    included_nodes = list()
    num_nodes = len(nodes)
    cost = 0

    included_nodes.append(nodes[0])
    nodes.remove(nodes[0])

    while len(included_nodes) < num_nodes:
        minimum = float('inf')
        not_included = -1
        for m in included_nodes:
            for n in nodes:
                if minimum > graph[m][n]:
                    minimum = graph[m][n]
                    not_included = n
        # print(f'Adding node: {not_included} with cost {minimum}, Included are: {included_nodes}, Cost is {cost}')
        included_nodes.append(not_included)
        nodes.remove(not_included)
        cost += minimum
    # print(f'MST cost: {cost}')
    return cost

class Micko(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        queue = []
        heapq.heappush(queue, PqNode(0, [0]))
        astar_path = [0]
        while len(queue) > 0:
            cur_path = heapq.heappop(queue).path
            if len(cur_path) < len(coin_distance[0]):
                # the if condition will assure that there is no zero, add heuristic for priority
                index = 0
                while index < len(coin_distance[0]):
                    if index not in cur_path:
                        new_path = [*cur_path, index]
                        heapq.heappush(queue, PqNode(calculate_path_cost(new_path, coin_distance) + modified_mst_Prim_cost(coin_distance, new_path), new_path))
                    index += 1
            elif len(cur_path) == len(coin_distance[0]):
                # looking for zero to terminate, no need for heuristics here
                new_path = [*cur_path, 0]
                heapq.heappush(queue, PqNode(calculate_path_cost(new_path, coin_distance), new_path))
            else:
                # found the optimal path
                astar_path = cur_path
                break
        return astar_path

