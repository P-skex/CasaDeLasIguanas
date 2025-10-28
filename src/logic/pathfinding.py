import heapq
import pygame

TILE_SIZE = 16

class Node:
    """Una clase de nodo para el algoritmo A*."""
    def __init__(self, position, parent=None):
        self.parent = parent
        self.position = position
        self.g = 0  # Distancia desde el nodo inicial
        self.h = 0  # Distancia heurística hasta el nodo final
        self.f = 0  # Costo total (g + h)

    def __eq__(self, other):
        return self.position == other.position

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        # Hacemos hash por posición para poder usar nodos en sets
        return hash(self.position)

def is_walkable(mundo, position):
    """Verifica si una posición de tile dada es caminable."""
    tile_x, tile_y = position
    
    # 1. Verificar si está dentro de los límites del mapa
    if not (0 <= tile_x < mundo.width and 0 <= tile_y < mundo.height):
        return False
        
    # 2. Verificar contra el 'set' de colisiones de tiles (agua, montañas, etc.)
    # Esta comprobación es súper rápida (O(1) en promedio)
    if (tile_x, tile_y) in mundo.colision_tiles:
        return False  # El tile está en la capa de colisiones
            
    # 3. Comprobación de objetos eliminada
    
    return True

def a_star(mundo, start, end):
    """Devuelve una lista de tuplas como una ruta desde el inicio hasta el fin."""
    open_list = []
    closed_set = set()
    start_node = Node(start)
    end_node = Node(end)
    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)
        closed_set.add(current_node.position)

        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            if not is_walkable(mundo, node_position) or node_position in closed_set:
                continue

            new_node = Node(node_position, current_node)
            new_node.g = current_node.g + 1
            new_node.h = abs(new_node.position[0] - end_node.position[0]) + abs(new_node.position[1] - end_node.position[1])
            new_node.f = new_node.g + new_node.h

            if any(n for n in open_list if new_node == n and new_node.g >= n.g):
                continue
            
            heapq.heappush(open_list, new_node)
    
    return None