# Implementation of a Max-Heap from scratch

class PriorityQueue:
    """
    Una implementación de una Cola de Prioridad usando un Max-Heap.
    Los elementos con mayor prioridad "flotan" hacia la cima.
    """
    def __init__(self):
        # El heap se almacena como una lista de Python.
        self.heap = []

    def push(self, item):
        """
        Agrega un elemento a la cola y lo ordena en el heap.
        Complejidad: O(log n)
        """
        self.heap.append(item)
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """
        Elimina y retorna el elemento con la mayor prioridad (la raíz del heap).
        Complejidad: O(log n)
        """
        if self.is_empty():
            raise IndexError("pop from an empty priority queue")
        
        self._swap(0, len(self.heap) - 1)
        max_item = self.heap.pop()
        if not self.is_empty():
            self._sift_down(0)
        return max_item

    def peek(self):
        """
        Retorna el elemento de mayor prioridad sin eliminarlo.
        Complejidad: O(1)
        """
        if self.is_empty():
            return None
        return self.heap[0]

    def is_empty(self):
        """Verifica si la cola está vacía."""
        return len(self.heap) == 0
        
    def __len__(self):
        return len(self.heap)

    # --- Métodos auxiliares privados ---

    def _swap(self, i, j):
        """Intercambia dos elementos en el heap."""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _parent(self, i):
        return (i - 1) // 2

    def _left_child(self, i):
        return 2 * i + 1

    def _right_child(self, i):
        return 2 * i + 2

    def _sift_up(self, i):
        """
        Mueve un elemento hacia arriba en el árbol hasta que la propiedad del
        heap se restablezca.
        """
        parent_index = self._parent(i)
        # Mientras no seamos la raíz y seamos "mayores" que nuestro padre...
        # Nota: La clase Tarea define la comparación con __lt__
        while i > 0 and self.heap[i] < self.heap[parent_index]:
            self._swap(i, parent_index)
            i = parent_index
            parent_index = self._parent(i)

    def _sift_down(self, i):
        """
        Mueve un elemento hacia abajo en el árbol hasta que la propiedad del
        heap se restablezca.
        """
        max_index = i
        left = self._left_child(i)
        if left < len(self.heap) and self.heap[left] < self.heap[max_index]:
            max_index = left

        right = self._right_child(i)
        if right < len(self.heap) and self.heap[right] < self.heap[max_index]:
            max_index = right

        if i != max_index:
            self._swap(i, max_index)
            self._sift_down(max_index)
