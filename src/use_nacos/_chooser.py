"""Weighted random chooser for instance selection.

This module implements a weighted random selection algorithm for
choosing among multiple service instances based on their weights.
"""

import random
from typing import Any, List, Tuple


class Chooser:
    """Weighted random chooser for instance selection.

    This class implements a weighted random selection algorithm that
    selects items based on their relative weights. Items with higher
    weights have a higher probability of being selected.

    Example:
        >>> hosts = [("instance1", 3.0), ("instance2", 1.0)]
        >>> chooser = Chooser(hosts)
        >>> chooser.refresh()
        >>> selected = chooser.random_with_weight()
    """

    def __init__(self, host_with_weight: List[Tuple[Any, float]]) -> None:
        """Initialize the chooser with weighted items.

        Args:
            host_with_weight: List of (item, weight) tuples.
        """
        self.host_with_weight = host_with_weight
        self.items: List[Any] = []
        self.weights: List[float] = []

    def refresh(self) -> None:
        """Compute cumulative weights for random selection.

        This method must be called before random_with_weight().

        Raises:
            ValueError: If the cumulative weights don't sum to 1.
        """
        origin_weight_sum = 0.0
        # Preparing the valid items list and calculating the original weights sum
        for item, weight in self.host_with_weight:
            if weight <= 0:
                continue
            if float("inf") == weight:
                weight = 10000.0
            elif float("nan") == weight:
                weight = 1.0
            origin_weight_sum += weight
            self.items.append(item)

        if not self.items:
            return

        # Computing the exact weights for each item
        exact_weights = []
        for _, weight in self.host_with_weight:
            if weight > 0:
                exact_weights.append(weight / origin_weight_sum)

        # Initializing the cumulative weights array
        random_range = 0.0
        for single_weight in exact_weights:
            random_range = random_range + single_weight
            self.weights.append(random_range)

        # Checking the final weight
        double_precision_delta = 0.0001
        if abs(self.weights[-1] - 1) < double_precision_delta:
            return
        raise ValueError(
            "Cumulative Weight calculate wrong, the sum of probabilities "
            "does not equal 1."
        )

    def random_with_weight(self) -> Any:
        """Select an item using weighted random selection.

        Returns:
            A randomly selected item based on weights.

        Note:
            refresh() must be called before this method.
        """
        # Generating a random number between 0 and 1
        random_value = random.random()

        # Using binary search to find the index for the random value
        index = self._find_index(self.weights, random_value)

        return self.items[index]

    @staticmethod
    def _find_index(weights: List[float], value: float) -> int:
        """Find the index where the value should be placed.

        Uses binary search to find the correct position in the
        cumulative weights array.

        Args:
            weights: Cumulative weights array.
            value: Random value to find position for.

        Returns:
            Index where the value falls in the weight ranges.
        """
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
