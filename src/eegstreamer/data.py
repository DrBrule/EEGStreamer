import json
import time
from math import floor

from numpy import ndarray


class EEGData(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timestamp = time.time_ns()

    # return timestamp in milliseconds
    @property
    def timestamp(self):
        return floor(self._timestamp/1e6)

    def __str__(self):
        return "{} @ {}".format(super().__str__(), self.timestamp)

    def json(self):

        serialized = {}

        for k, v in self.items():
            if isinstance(v, ndarray):
                v = v.tolist()
            serialized[k] = v

        return json.dumps({
            'timestamp': self.timestamp,
            'data': serialized
        })
