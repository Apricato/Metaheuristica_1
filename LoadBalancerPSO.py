import random

# PSO parameters
NUM_PARTICLES = 12
NUM_PROCESSORS = 8
# PROCESSOR_WEIGHTS = [1, 1, 1, 1, 1, 1, 1, 1]
TOTAL_TASKS = 100000
TASKS_PER_INTERVAL = 10000
CURRENT_TASKS_FOR_LOGGING = 10000
TASKS_FOR_LOGGING = 10000
COGNITIVE_FACTOR = 2
SOCIAL_FACTOR = 2
INERTIA_WEIGHT = 0.9

# We create a particle class to represent an individual way of assigning tasks to processors
# Each particle has a random initial position, and develops a velocity that will help it move towards the best solution
class Particle:
    def __init__(self):
        # Initialize positions (tasks assigned to processors)
        self.position = self.random_task_assignment(NUM_PROCESSORS, TOTAL_TASKS)
        
        # Initialize velocities to zeros
        self.velocity = [0.0] * NUM_PROCESSORS
        
        # Initialize personal best
        self.best_position = self.position[:]
        self.best_fitness = self.evaluate_fitness(self.position)
        
        # Tasks processed by each processor
        self.tasks_processed = [0] * NUM_PROCESSORS

    def random_task_assignment(self, num_processors, total_tasks):
        # Randomly divide total_tasks into num_processors parts
        random_numbers = [random.random() for _ in range(num_processors)]
        sum_random_numbers = sum(random_numbers)
        fractions = [x / sum_random_numbers for x in random_numbers]
        tasks = [int(round(f * total_tasks)) for f in fractions]
        
        # Adjust to ensure the sum equals total_tasks
        # For each processor determine if the difference is positive or negative, then add or remove tasks based on it
        diff = total_tasks - sum(tasks)
        while diff != 0:
            for i in range(num_processors):
                if diff == 0:
                    break
                if diff > 0:
                    tasks[i] += 1
                    diff -= 1
                elif tasks[i] > 0:
                    tasks[i] -= 1
                    diff += 1
        print(f'Initial tasks {tasks}')
        return tasks

    # Fitness is just how far away the current load is from the mean load
    def evaluate_fitness(self, position):
        # Fitness is the variance of tasks assigned to processors based on the mean load and their current load
        mean_load = sum(position) / len(position)
        # I wanted to add variance for considering error margins in the load balancing but it wasn't working :(
        # variance = (sum((x - mean_load) ** 2 for x in position) / len(position)) ** 0.5
        return mean_load 

    # Update the velocity of the particle based on the best local and global fitness
    # We use the regular formula weight * velocity + cognitive * r1 * (best_local - position) + social * r2 * (best_global - position)
    def update_velocity(self, global_best_position):
        mean_load = sum(self.position) / len(self.position)
        load_balance_factor = 0.5  # Adjust this factor as needed
        for i in range(NUM_PROCESSORS):
            r1 = random.random()
            r2 = random.random()
            best_local_fitness = self.evaluate_fitness(self.best_position)
            best_global_fitness = self.evaluate_fitness(global_best_position)
            cognitive = COGNITIVE_FACTOR * r1 * (best_local_fitness - self.position[i])
            social = SOCIAL_FACTOR * r2 * (best_global_fitness - self.position[i])
            # Additional term to balance the load towards mean_load
            load_balance = load_balance_factor * (mean_load - self.position[i])
            # At this point, velocity can be very large or very small, and the sign represents the direction to change (add or substract)
            self.velocity[i] = INERTIA_WEIGHT * self.velocity[i] + cognitive + social + load_balance

    # The position means the size of the load for each processor
    def update_position(self):
        # Approximate the number of tasks to be added to each processor based on their velocity
        weight_factor = TOTAL_TASKS - sum(self.tasks_processed)
        # Sometimes this can be zero, so we need to avoid division by zero
        if weight_factor == 0:
            weight_factor = 1
        # We create weights based on the velocity of each processor
        velocity_weights = [self.velocity[i] / weight_factor for i in range(NUM_PROCESSORS)]
        weights_sum = sum([abs(w) for w in velocity_weights])
        velocity_weights = [w / weights_sum for w in velocity_weights]
        mean_load = sum(self.position) / len(self.position)

        # Calculate the number of tasks that can actually be redistributed
        redistributable_tasks = sum([max(0, p - mean_load) for p in self.position])
        
        # Compute the number of tasks to be potentially added or substracted to each processor
        added_tasks = [int(round(weight * redistributable_tasks)) for weight in velocity_weights]
        
        # Re-balance the potential tasks based on the actual number of tasks that can be redistributed
        self.position = [self.position[i] + added_tasks[i] for i in range(NUM_PROCESSORS)]
        self.position = [int(round(p)) for p in self.position]
        self.adjust_position()

    # Adjust the position by removing or adding tasks when the weights create a surplus or a deficit
    # This is done by adding or removing tasks from a random processor until the surplus is exhausted
    def adjust_position(self):
        total_diff = TOTAL_TASKS - sum(self.tasks_processed)
        surplus_tasks = total_diff - sum(self.position)
        while surplus_tasks < 0: # there are extra tasks that shouldn't be there
            self.position[random.randint(0, NUM_PROCESSORS - 1)] -= 1
            surplus_tasks += 1
        while surplus_tasks > 0: # there are taks that were removed
            self.position[random.randint(0, NUM_PROCESSORS - 1)] += 1
            surplus_tasks -= 1
        
        # Ensure no negative assignments
        for i in range(len(self.position)):
            if self.position[i] < 0:
                surplus_tasks += -self.position[i]
                self.position[i] = 0

    # Simulate a task being processed, removing one from each of the processors
    def process_tasks(self):
        self.tasks_processed = [t + 1 if p > 0 else t for t, p in zip(self.tasks_processed, self.position)]
        self.position = [p - 1 for p in self.position]
        self.adjust_position()

    def is_complete(self):
        return all(self.position[i] <= 0 for i in range(len(self.position)))

class PSO:
    def __init__(self):
        self.particles = [Particle() for _ in range(NUM_PARTICLES)]
        # Initialize global best
        self.global_best_particle = min(self.particles, key=lambda p: p.best_fitness)
        self.global_best_position = self.global_best_particle.best_position[:]

    def run(self):
        # Continue until all tasks are processed
        all_tasks_completed = False
        interval = 0
        global CURRENT_TASKS_FOR_LOGGING

        while not all_tasks_completed:
            all_tasks_completed = True
            interval += 1
            should_increase_logging_threshold = False

            for particle_idx, particle in enumerate(self.particles):
                # Process tasks
                particle.process_tasks()
                # print(f'Particle {particle_idx} has processed {sum(particle.tasks_processed)} tasks and has {sum(particle.position)} tasks remaining')
                # for processor_idx, processor_load in enumerate(particle.position):
                #     print(f'Processor {processor_idx} has {processor_load} tasks remaining')

                total_tasks_processed = sum(particle.tasks_processed)
                if total_tasks_processed >= CURRENT_TASKS_FOR_LOGGING:
                    print(f'Particle {particle_idx} has processed {total_tasks_processed} tasks'
                          f' with current loads:')
                    for processor_idx, processor_load in enumerate(particle.position):
                        print(f'Processor {processor_idx} has {processor_load} tasks remaining')
                    
                    should_increase_logging_threshold = True

                # Update all_tasks_completed flag
                if not particle.is_complete():
                    all_tasks_completed = False

                # Update velocities and positions
                particle.update_velocity(self.global_best_position)
                particle.update_position()

                # Evaluate fitness
                fitness = particle.evaluate_fitness(particle.position)

                # Update personal best
                if fitness < particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = particle.position[:]

                # Update global best
                if fitness < self.global_best_particle.best_fitness:
                    self.global_best_particle = particle
                    self.global_best_position = particle.position[:]
            
            if should_increase_logging_threshold:
                CURRENT_TASKS_FOR_LOGGING += TASKS_FOR_LOGGING

# Run the PSO simulation
if __name__ == "__main__":
    pso = PSO()
    pso.run()
