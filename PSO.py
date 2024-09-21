# Create a Particle Swarm Optimization-based algorithm that distributes the loads from 100,000 tasks each taking 1 second, to 8 processors. The algorithm should minimize the total time taken to complete all tasks. The algorithm should be implemented in Python and should be able to run on a single machine with 8 processors
from random import randint, random

particles = 100
processors = 8
tasks = 100000
task_time = 1
max_iterations = 1000
c1 = 2
c2 = 2
w = 0.9

class Particle:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity
        self.best_position = position
        self.best_score = float('inf')
    
    def update_position(self):
        self.position = [max(0, min(p, tasks)) for p in self.position]
    
    def update_velocity(self, global_best_position):
        self.velocity = [w*v + c1*random()*(bp-p) + c2*random()*(global_best_position[i]-p) for i, (p, v, bp) in enumerate(zip(self.position, self.velocity, self.best_position))]
    
    def update_best(self, score):
        if score < self.best_score:
            self.best_position = self.position
            self.best_score = score
    
    def __str__(self):
        return f'Position: {self.position}, Best Position: {self.best_position}, Best Score: {self.best_score}'
    
    def __repr__(self):
        return str(self)
    
class PSO:
    def __init__(self):
        self.particles = [Particle([randint(0, tasks) for _ in range(processors)], [0 for _ in range(processors)]) for _ in range(particles)]
        self.global_best_position = self.particles[0].position
        self.global_best_score = float('inf')
    
    def run(self):
        for _ in range(max_iterations):
            for particle in self.particles:
                score = self.evaluate(particle)
                particle.update_best(score)
                if score < self.global_best_score:
                    self.global_best_position = particle.position
                    self.global_best_score = score
                particle.update_velocity(self.global_best_position)
                particle.update_position()
    
    def evaluate(self, particle):
        return sum([p*task_time for p in particle.position])
    
    def __str__(self):
        return f'Global Best Position: {self.global_best_position}, Global Best Score: {self.global_best_score}'
    
    def __repr__(self):
        return str(self)

pso = PSO()
pso.run()
print(pso)