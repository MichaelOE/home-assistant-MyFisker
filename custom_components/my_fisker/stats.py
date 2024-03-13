from collections import deque
import logging
import time

_LOGGER = logging.getLogger(__name__)


class TravelStats(object):
    """Travel stats for last journey."""

    def __init__(self):
        # _LOGGER.debug("TravelStats init")
        self.vehicleParked = True
        self.qDist = deque()
        self.qBatt = deque()

    def Clear(self):
        self.qBatt.clear()
        self.qDist.clear()

    def GetTravelStart(self):
        if self.vehicleParked:
            return None

        return self.qDist[0].value

    def GetTravelTime(self):
        if self.vehicleParked:
            return None

        tt = self.qDist[-1].timestamp - self.qDist[0].timestamp
        return time.strftime("%Hh:%Mm:%Ss", time.gmtime(tt))

    def GetTravelBatt(self):
        if self.vehicleParked:
            return None

        batt = self.qBatt[0].value - self.qBatt[-1].value
        return batt

    def GetTravelDist(self):
        if self.vehicleParked:
            return None

        dist = self.qDist[-1].value - self.qDist[0].value
        return dist

    def GetEfficiency(self):
        if self.vehicleParked:
            return None

        dist = self.qDist[-1].value - self.qDist[0].value
        batt = self.qBatt[0].value - self.qDist[-1].value
        return dist / batt

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
    def timeStamp(self):
        return self._time
