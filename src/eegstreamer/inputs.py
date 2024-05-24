import csv
import json
import os
from abc import ABC, abstractmethod
import asyncio
import random
import traceback
from logging import getLogger
from typing import Union
from muselsl.muse import Muse

from eegstreamer import DeviceConnectionFailure, DataStreamInterrupted
from eegstreamer.data import EEGData
from eegstreamer.outputs import EEGOutputStreamer
from eegstreamer.transforms import EEGTransformer

import numpy as np
from scipy import signal
from time import time

logger = getLogger(__name__)


class EEGInputStreamer(ABC):

    def __init__(self):

        self.outputs = []

    def connect(self, stream: Union[EEGTransformer, EEGOutputStreamer]):
        self.outputs.append(stream)

    async def send(self, data) -> None:
        # TODO : if one of the outputs raises an exception, should all outputs halt?
        for output in self.outputs:
            await output.receive(data)

    @abstractmethod
    async def start(self, duration: int = 0):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class RandomEEGInputStream(EEGInputStreamer):

    def __init__(self, sample_rate: int = 10, channel_count=2):
        super().__init__()
        self._sample_rate = sample_rate
        self._channel_count = channel_count

    async def close(self):
        pass

    async def stop(self):
        pass

    async def start(self, duration: int = 0):
        sample_count = self._sample_rate * duration

        samples = 0
        while not sample_count or samples < sample_count:
            sample_data = dict()
            packet = list()
            for channel in range(0, self._channel_count):
                value = random.randint(-10, 10)
                sample_data[f"channel{channel}"] = value
                packet.append(value)

            sample_data['packet'] = packet

            await self.send(EEGData(sample_data))
            samples += 1
            await asyncio.sleep(1 / self._sample_rate)


class FileEEGInputStreamer(EEGInputStreamer, ABC):

    def __init__(self, filename, sample_rate: int = 256):
        super().__init__()
        self.sample_rate = sample_rate
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Could not find: {filename}")
        self.filename = filename
        self.file_handle = None

    def get_file_handle(self):
        return open(self.filename, mode='r')

    async def stop(self):
        pass

    async def close(self):
        self.file_handle.close()
        await asyncio.sleep(0)


class JSONFileInputStreamer(FileEEGInputStreamer):

    async def start(self, duration: int = 0):

        if not self.file_handle:
            self.file_handle = self.get_file_handle()

        for line in self.file_handle:
            eeg_data = json.loads(line)
            await self.send(EEGData(eeg_data['data']))
            await asyncio.sleep(1/self.sample_rate)


class CSVFileInputStreamer(FileEEGInputStreamer):

    def __init__(self, filename, sample_rate: int = 256):
        super().__init__(filename, sample_rate)
        self.csvreader = None

    async def start(self, duration: int = 0):
        logger.info("starting csv file reader")
        self.file_handle = self.get_file_handle()
        self.csvreader = csv.reader(self.file_handle)
        keys = None
        row_count = 0
        for row in self.csvreader:
            if not keys:
                keys = row
                keys.pop(0)
            else:

                floats = [float(c) for c in row[1:]]
                data = dict(zip(keys, floats))
                data['packet'] = np.array(floats)
                await self.send(EEGData(data))
                await asyncio.sleep(1 / self.sample_rate)
                row_count += 1

        logger.debug(f"done with all rows: {row_count}")


class FakeEEGDeviceInputStreamer(EEGInputStreamer):

    def __init__(self, sample_rate: int = 256, device:str = None):
        """
        Parameters
        ----------
            sample_rate : int
                in hertz
        """
        super().__init__()
        self._sample_rate = sample_rate
        self._device = device
    
    async def start(self, duration: int = 0):
        sample_count = self._sample_rate * duration

        if self._device == 'muse':
            channels = ["TP9",  "AF7", "AF8" , "TP10"]
        elif self._device == 'crown':
            channels = ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"]
        else:
            channels = ["TP9", "AF7", "AF8", "TP10"]

        # prep filters
        sos = signal.butter(2, [.01, 100], 'bandpass', output='sos', fs=self._sample_rate)

        # init one second of data for filtering purposes and filter it to match subsequent data
        last_second = ( np.random.rand( 256 , len(channels) ) * 1000 ) + 200
        last_second = signal.sosfilt(sos, last_second)
        samples = 0
        while not sample_count or samples < sample_count:
            batch = (np.random.rand( 1 , len(channels) ) * 1000) + 200
            # last_second = np.delete(last_second, [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], 0)
            last_second = np.delete(last_second, [0], 0)
            last_second = np.append(last_second, batch, 0)
            y_sos = signal.sosfilt(sos, last_second)

            data = dict(zip(channels, np.array(y_sos[255, :])))
            data['packet'] = np.array(y_sos[255, :])

            data = EEGData(data)
            await self.send(data)
            samples += 1
            await asyncio.sleep(1/self._sample_rate)
      
    async def close(self):
        pass

    async def stop(self):
        pass


class MuseInputStreamer(EEGInputStreamer):

    CHANNELS = ["TP9",  "AF7" , "AF8" , "TP10"]

    def __init__(self, mac_address, name, interface, event_loop=None, backend='bgapi', disconnect_delay=10):
        super().__init__()
        self.event_loop = event_loop
        self._disconnect_delay = disconnect_delay

        def push_eeg(data, timestamps):
            for ii in range(data.shape[1]):
                packet = data[:, ii]
                d = dict(zip(self.CHANNELS, packet))
                d['packet'] = packet[0:4] # the muse comes back with 5 values, even through there are only 4 sensors
                task = asyncio.run_coroutine_threadsafe(self.send(EEGData(d)), loop=event_loop)
                # if the outputs downstream have an issue, bubble up through error message
                # ( raising the exception will cause the muse streamer thread to exit )
                try:
                    r = task.result()
                except:  # noqa
                    e = task.exception()
                    logger.error("".join(traceback.TracebackException.from_exception(e).format()))

        self.muse = Muse(address=mac_address, callback_eeg=push_eeg, backend=backend, interface=interface, name=name)

    async def start(self, sample_duration: int = 0):
        is_connected = self.muse.connect()

        if is_connected:
            self.muse.start()

            while time() - self.muse.last_timestamp < self._disconnect_delay:
                try:
                    await asyncio.sleep(1)
                except KeyboardInterrupt:
                    await self.close()
                    break
            logger.error("no longer receiving data from muse")
            raise DataStreamInterrupted()
        else:
            raise DeviceConnectionFailure()

    async def stop(self):
        self.muse.stop()

    async def close(self):
        self.muse.stop()
        self.muse.disconnect()
