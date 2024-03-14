from collections import deque
import logging
import time

_LOGGER = logging.getLogger(__name__)


class TripStats(object):
    """Travel stats for last journey."""

    def __init__(self):
        # _LOGGER.debug("TravelStats init")
        self.vehicleParked = True
        self.Clear()

    def Clear(self):
        self.qDist = deque()
        self.qBatt = deque()
        self._batt = 0
        self._time = 0
        self._dist = 0
        self._efficiency = 0

    def GetTravelStart(self):
        if self.vehicleParked:
            return None

        return self.qDist[0].value

    def GetTravelTime(self):
        if self.vehicleParked:
            return self._time

        self._time = self.qDist[-1].timestamp - self.qDist[0].timestamp
        # return time.strftime("%Hh:%Mm:%Ss", time.gmtime(tt))
        return self._time

    def GetTravelBatt(self):
        if self.vehicleParked:
            return self._batt

        self._batt = self.qBatt[0].value - self.qBatt[-1].value
        return self._batt

    def GetTravelDist(self):
        if self.vehicleParked:
            return self._dist

        self._dist = self.qDist[-1].value - self.qDist[0].value
        return self._dist

    def GetEfficiency(self):
        #if self.vehicleParked:
            #return self._efficiency

        # dist = self.qDist[-1].value - self.qDist[0].value
        # batt = self.qBatt[0].value - self.qBatt[-1].value
        return self._dist / self._batt

    def AddBattery(self, batt):
        item = StatsItem(batt, time.time())
        self.qBatt.append(item)

    def AddDistance(self, dist):
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
