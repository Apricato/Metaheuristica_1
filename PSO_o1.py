import random
import numpy as np

# PSO parameters
NUM_PARTICLES = 1000
NUM_PROCESSORS = 8
TOTAL_TASKS = 100000
TASKS_PER_INTERVAL = 10000
COGNITIVE_FACTOR = 2
SOCIAL_FACTOR = 2
INERTIA_WEIGHT = 0.9

class Particle:
    def __init__(self):
        # Initialize positions (tasks assigned to processors)
        self.position = [random.random() for _ in range(NUM_PROCESSORS)]
        self.position = [x / sum(self.position) * TOTAL_TASKS for x in self.position]
        self.position = [int(round(x)) for x in self.position]

        # Total tasks assigned (should remain TOTAL_TASKS)
        self.total_tasks = TOTAL_TASKS

        # Ensure the sum equals TOTAL_TASKS
        self.adjust_position()

        # Initialize velocities
        self.velocity = [0 for _ in range(NUM_PROCESSORS)]

        # Initialize personal best
        self.best_position = self.position.copy()
        self.best_fitness = self.evaluate_fitness()

        # Tasks processed by each processor
        self.tasks_processed = [int(0) for _ in range(NUM_PROCESSORS)]

    def adjust_position(self):
        # Ensure no negative assignments
        self.position = [max(x, 0) for x in self.position]

        # Adjust to ensure the sum equals TOTAL_TASKS
        total = sum(self.position)
        if total != self.total_tasks:
            diff = self.total_tasks - total
            # Distribute the difference
            for i in range(abs(int(diff))):
                idx = i % NUM_PROCESSORS
                if diff > 0:
                    self.position[idx] += 1
                elif self.position[idx] > 0:
                    self.position[idx] -= 1

    def evaluate_fitness(self):
        # Fitness is the maximum total tasks assigned to any processor
        return max(self.position)

    def update_velocity(self, global_best_position):
        r1 = [random.random() for _ in range(NUM_PROCESSORS)]
        r2 = [random.random() for _ in range(NUM_PROCESSORS)]
        cognitive = [COGNITIVE_FACTOR * r1[i] * (self.best_position[i] - self.position[i]) for i in range(NUM_PROCESSORS)]
        social = [SOCIAL_FACTOR * r2[i] * (global_best_position[i] - self.position[i]) for i in range(NUM_PROCESSORS)]
        self.velocity = [INERTIA_WEIGHT * self.velocity[i] + cognitive[i] + social[i] for i in range(NUM_PROCESSORS)]

    def update_position(self):
        # Update position with velocity
        self.position = self.position + self.velocity

        # Ensure positions are integers
        self.position = [int(round(x)) for x in self.position]

        # Ensure positions are >= tasks already processed
        self.position = [max(x, y) for x, y in zip(self.position, self.tasks_processed)]

        # Adjust positions to maintain total tasks
        self.adjust_position()

class PSO:
    def __init__(self):
        self.particles = [Particle() for _ in range(NUM_PARTICLES)]
        # Initialize global best
        self.global_best_particle = min(self.particles, key=lambda p: p.best_fitness)
        self.global_best_position = self.global_best_particle.best_position.copy()

    def run(self):
        # Continue until all tasks are processed
        all_tasks_completed = False
        interval = 0

        while not all_tasks_completed:
            all_tasks_completed = True
            interval += 1

            for particle_idx, particle in enumerate(self.particles):
                # Each processor processes up to TASKS_PER_INTERVAL or remaining tasks
                processors_completed = True
                for proc_idx in range(NUM_PROCESSORS):
                    remaining_tasks = particle.position[proc_idx] - particle.tasks_processed[proc_idx]
                    if remaining_tasks > 0:
                        delta = min(TASKS_PER_INTERVAL, remaining_tasks)
                        particle.tasks_processed[proc_idx] += delta
                        processors_completed = False

                        # Log progress
                        print(f"Interval {interval}: Particle {particle_idx}, Processor {proc_idx}, "
                              f"Tasks Processed: {particle.tasks_processed[proc_idx]}, "
                              f"Total Assigned: {particle.position[proc_idx]}")

                # Update all_tasks_completed flag
                if not processors_completed:
                    all_tasks_completed = False

                # Update velocities and positions
                particle.update_velocity(self.global_best_position)
                particle.update_position()

                # Evaluate fitness
                fitness = particle.evaluate_fitness()

                # Update personal best
                if fitness < particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = particle.position.copy()

                # Update global best
                if fitness < self.global_best_particle.best_fitness:
                    self.global_best_particle = particle
                    self.global_best_position = particle.position.copy()

# Run the PSO simulation
if __name__ == "__main__":
    pso = PSO()
    pso.run()
