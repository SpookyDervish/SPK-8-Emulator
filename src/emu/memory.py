class Memory:
    def __init__(self, size=2**16):
        self.data = []

        for i in range(size):
            self.data.append(0x0)