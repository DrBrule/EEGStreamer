import json
from json import JSONEncoder

from numpy import ndarray

from eegstreamer.data import EEGData


class EEGStreamJSONEncoder(JSONEncoder):

    @classmethod
    def default(cls, o):
        if isinstance(o, EEGData):
            o.json()
        elif isinstance(o, ndarray):
            json.dumps(o.tolist())
        else:
            return o.__dict__
