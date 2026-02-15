class Star:
    def __init__(self, name, mass, radius):
        self.name = name
        self.mass = mass
        self.radius = radius

    def calculate_g(self):
        G = 6.67e-11

        g = (G * self.mass)
        return g