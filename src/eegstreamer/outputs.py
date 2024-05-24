import json
from abc import ABC, abstractmethod
import os.path
import numpy

from aiohttp import ClientSession
import asyncio
from pythonosc.udp_client import SimpleUDPClient
from pprint import pprint as pp

from eegstreamer.data import EEGData

import csv



class EEGOutputStreamer(ABC):

    def __init__(self):
        pass

    @abstractmethod
    async def receive(self, data: dict) -> None:
        pass

    @abstractmethod
    def close(self):
        pass


class ScreenEEGOutputStreamer(EEGOutputStreamer):

    def __init__(self):
        super().__init__()
        self.samples_printed = 0

    def sample_count(self):
        return self.samples_printed

    async def receive(self, data: EEGData) -> None:
        pp(data['packet'])
        self.samples_printed += 1

    def close(self):
        pass


class FileOutputStreamer(EEGOutputStreamer, ABC):

    def __init__(self, filename: str, append: bool = False):
        super().__init__()
        self.filename = os.path.abspath(filename)
        if os.path.exists(self.filename) and not append:
            raise FileExistsError(f"'{self.filename}' exists but not in append mode")
        self.append = append
        storage_dir = os.path.dirname(self.filename)
        if not os.path.exists(storage_dir):
            raise NotADirectoryError("'{}' does not exist for writing".format(storage_dir))
        self.file_handle = None

    def get_file_handle(self):
        return open(self.filename, mode='a' if self.append else 'w')

    async def close(self):
        self.file_handle.close()
        await asyncio.sleep(0)


class JSONFileOutputStreamer(FileOutputStreamer):

    async def receive(self, data: EEGData) -> None:
        if not self.file_handle:
            self.file_handle = self.get_file_handle()

        self.file_handle.write(data.json())
        self.file_handle.write("\n")


class CSVFileOutputStreamer(FileOutputStreamer):

    def __init__(self, filename, append=False):
        super().__init__(filename, append)
        self.csvwriter = None

    async def receive(self, data: EEGData) -> None:

        if not self.csvwriter:

            self.file_handle = self.get_file_handle()
            self.csvwriter = csv.writer(self.file_handle, dialect='unix')
            self.csvwriter.writerow(["timestamp", "TP9",  "AF7", "AF8", "TP10"])

        csv_row = [data.timestamp, ] + data['packet'].tolist()

        self.csvwriter.writerow(csv_row)
        await asyncio.sleep(0)


class HttpPostEEGOutputStreamer(EEGOutputStreamer):

    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        self.session = ClientSession()

    async def receive(self, data: dict) -> None:
        response = await self.session.post(self.endpoint, data=json.dumps(data))
        if response.status != 200:
            raise Exception()

    async def close(self):
        await self.session.close()


class WebsocketEEGOutputStreamer(EEGOutputStreamer):

    def __init__(self):
        super().__init__()

    async def receive(self, data: dict) -> None:
        pass

    async def close(self):
        pass


class OscOutputStreamer(EEGOutputStreamer):

    clients = {}

    def __init__(self, ip='127.0.0.1', port=1337, address="/eeg", multi_channel=True):
        super().__init__()
        self._ip = ip
        self._port = port
        self._address = address
        self._multi_channel = multi_channel

        if port not in self.clients:
            self.clients[port] = SimpleUDPClient(self._ip, self._port)  # Create client

    VALID_TYPES = [list, tuple, int, float, numpy.float64, numpy.ndarray, str]

    async def receive(self, data: EEGData) -> None:

        for key, value in data.items():
            if key == 'packet' and type(value) in self.VALID_TYPES:
                for client in self.clients.values():
                    client.send_message(self._address, data['packet'])
            elif type(value) in self.VALID_TYPES and self._multi_channel:
                address = f"{self._address}/{key}"
                for client in self.clients.values():
                    client.send_message(address, [value, ])
            else:
                raise ValueError("sending an incompatible data type of '{}' for '{}'".format(type(value), key))

        await asyncio.sleep(0)

    async def close(self):
        pass
