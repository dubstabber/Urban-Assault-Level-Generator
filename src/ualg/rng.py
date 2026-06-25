"""MSVCRT-compatible pseudo-random number generator."""

from __future__ import annotations

import time


class MSVCRTRandom:
    """Visual C++ 6.0 `rand`/`srand` compatible generator."""

    _MULTIPLIER = 214013
    _INCREMENT = 2531011
    _MASK = 0x7FFFFFFF
    RAND_MAX = 0x7FFF

    def __init__(self, seed: int = 1) -> None:
        self._state = 1
        self.srand(seed)

    def srand(self, seed: int = 0) -> None:
        if seed == 0:
            seed = int(time.time())
        self._state = seed & self._MASK

    def rand(self) -> int:
        self._state = (self._MULTIPLIER * self._state + self._INCREMENT) & self._MASK
        return (self._state >> 16) & self.RAND_MAX

    def rand_mod(self, n: int) -> int:
        if n <= 0:
            return 0
        return self.rand() % n

    def rand_range(self, min_value: int, max_value: int) -> int:
        if min_value > max_value:
            min_value, max_value = max_value, min_value
        return min_value + self.rand_mod(max_value - min_value + 1)

    def rand_variation(self, delta: int) -> int:
        return self.rand_range(-delta, delta)

    def rand_float(self) -> float:
        return self.rand() / float(self.RAND_MAX + 1)

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, value: int) -> None:
        self._state = value & self._MASK

    def choice(self, values):
        if not values:
            raise IndexError("cannot choose from an empty sequence")
        return values[self.rand_mod(len(values))]
