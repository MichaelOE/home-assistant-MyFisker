from collections import deque
import logging
import time

_LOGGER = logging.getLogger(__name__)


class TripStats(object):
    """Trip stats for current drive."""

    def __init__(self):
        # _LOGGER.debug("TripStats init")
        self.carIsRunning = False
        self.vehicleParked = True
        self.qDist = deque()
        self.qBatt = deque()
        self._batt = 0
        self._time = 0
        self._dist = 0
        self._efficiency = 0
        self._speed = 0
        self.previous_efficiency = 0
        self.Clear()

    def Clear(self):
        self.previous_efficiency = self._efficiency
        self.qDist = deque()
        self.qBatt = deque()
        self._batt = 0
        self._time = 0
        self._dist = 0
        self._efficiency = 0
        self._speed = 0

    @property
    def start(self):
        if self.vehicleParked:
            return None

        return self.qDist[0].value

    @property
    def time(self):
        if not self.vehicleParked:
            self._time = self.qDist[-1].timestamp - self.qDist[0].timestamp

        return time.strftime("%HH:%Mm", time.gmtime(self._time))

    @property
    def batt(self):
        if not self.vehicleParked:
            self._batt = self.qBatt[0].value - self.qBatt[-1].value

        return self._batt

    @property
    def dist(self):
        if not self.vehicleParked:
            self._dist = self.qDist[-1].value - self.qDist[0].value

        return self._dist

    @property
    def efficiency(self):
        if self._dist != 0 and self._batt != 0:
            self._efficiency = self._batt / self._dist

        return round(self._efficiency, 2)

    @property
    def average_speed(self):
        if self._dist != 0 and self._time != 0:
            self._speed = self._dist / (self._time / 3600)

        return round(self._speed, 2)

    def add_battery(self, batt):
        item = StatsItem(batt, time.time())
        self.qBatt.append(item)

    def add_distance(self, dist):
        item = StatsItem(dist, time.time())
        self.qDist.append(item)


class StatsItem(object):
    def __init__(self, val: float, time: time) -> None:
        self._val = val
        self._time = time

    def __str__(self):
        return f"{self._val}:{self._time}"

    @property
    def value(self):
        return self._val

    @property
    def timestamp(self):
        return self._time
