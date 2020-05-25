from collections import deque

class Buffer:
    def __init__(self, cap, fn_on_delete = None):
        self.cap = cap
        self.q = deque()
        self.fn_on_delete = fn_on_delete

    def add(self, item):
        self.q.append(item)
        if len(self.q) > self.cap:
            clip = self.q.popleft()
            if self.fn_on_delete is not None:
                self.fn_on_delete(clip)

    def popleft(self):
        return self.q.popleft()

    def last(self):
        return self.q[-1]

    def clear(self):
        self.q.clear()

    def __len__(self):
        return len(self.q)

    def __getitem__(self, key):
        return self.q[key]
