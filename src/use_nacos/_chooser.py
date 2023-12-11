# created by gpt-4

import random


class Chooser:
    def __init__(self, host_with_weight: list):
        self.host_with_weight = host_with_weight
        self.items = []
        self.weights = []

    def refresh(self):
        origin_weight_sum = 0.0
        # Preparing the valid items list and calculating the original weights sum
        for item, weight in self.host_with_weight:
            if weight <= 0:
                continue
            if float('inf') == weight:
                weight = 10000.0
            elif float('nan') == weight:
                weight = 1.0
            origin_weight_sum += weight
            self.items.append(item)

        if not self.items:
            return

        # Computing the exact weights for each item
        exact_weights = [weight / origin_weight_sum for _, weight in self.host_with_weight if weight > 0]

        # Initializing the cumulative weights array
        random_range = 0.0
        for single_weight in exact_weights:
            random_range += single_weight
            self.weights.append(random_range)

        # Checking the final weight
        double_precision_delta = 0.0001
        if abs(self.weights[-1] - 1) < double_precision_delta:
            return
        raise ValueError("Cumulative Weight calculate wrong, the sum of probabilities does not equal 1.")

    def random_with_weight(self):
        # Generating a random number between 0 and 1
        random_value = random.random()

        # Using binary search to find the index for the random value
        index = self._find_index(self.weights, random_value)

        return self.items[index]

    def _find_index(self, weights, value):
        # Perform a binary search manually since weights are not just keys
        low = 0
        high = len(weights) - 1
        while low <= high:
            mid = (low + high) // 2
            if weights[mid] < value:
                low = mid + 1
            elif weights[mid] > value:
                high = mid - 1
            else:
                return mid  # This is the exact match case
        return low  # This is the case where value should be inserted
