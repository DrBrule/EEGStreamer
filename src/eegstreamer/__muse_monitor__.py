import argparse
import os
from asyncio import CancelledError
from time import sleep, time

from math import floor

from eegstreamer import DataStreamInterrupted
from eegstreamer.inputs import MuseInputStreamer
from eegstreamer.outputs import ScreenEEGOutputStreamer, CSVFileOutputStreamer, EEGOutputStreamer, OscOutputStreamer
from eegstreamer.transforms import PowerCoherenceEEGTransformer, DownSampleEEGTransformer
import asyncio
from colorama import Fore
from muselsl import list_muses

event_loop = asyncio.get_event_loop()



class TerminalOutputStreamer(EEGOutputStreamer):
    def __init__(self):
        super().__init__()
        self.start_time = time()
        self.samples = 0

    async def receive(self, data: dict) -> None:
        current_time = time()
        self.samples += 1
        elapsed_time = floor(current_time - self.start_time)
        elapsed_minutes = floor(elapsed_time / 60)
        elapsed_seconds = elapsed_time % 60
        line = f"{Fore.BLUE} samples acquired: {Fore.YELLOW} {self.samples} {Fore.BLUE} | elapsed: {Fore.YELLOW} {elapsed_minutes}:{elapsed_seconds:02d} {Fore.WHITE}"
        print('\r' + line, end='')

        await asyncio.sleep(0)
        sleep(0)

    def close(self):
        print("\n")


async def muse_streamer(sample_rate=None, mac_address=None, name=None, interface=None, downsample_scale=None, filename=None, osc_port=None):
    if not sample_rate:
        sample_rate = 256
    if not downsample_scale:
        downsample_scale = 256

    upstreams = []

    if osc_port:
        osc_eeg_output = OscOutputStreamer(address="/eeg", port=9807)
        osc_prc_output = OscOutputStreamer(address="/prc", port=9807)
        terminal_stream = TerminalOutputStreamer()

        pwrc_transformer = PowerCoherenceEEGTransformer()
        pwrc_transformer.connect(osc_prc_output)

        downsample_32 = DownSampleEEGTransformer(sample_rate=32)
        downsample_32.connect(osc_eeg_output)

        upstreams.append(pwrc_transformer)
        upstreams.append(downsample_32)
        upstreams.append(terminal_stream)

    elif not filename:
        # create the output stream
        output_stream = ScreenEEGOutputStreamer( )

        pcr_stream = PowerCoherenceEEGTransformer()
        # tell the transform stream where to send its data
        pcr_stream.connect(output_stream)
        upstreams.append(pcr_stream)
    else:
        output_stream = CSVFileOutputStreamer(filename)
        terminal_stream = TerminalOutputStreamer()
        upstreams.append(output_stream)
        upstreams.append(terminal_stream)

    # create the input stream
    input_stream = MuseInputStreamer(mac_address, name, interface, event_loop=event_loop)

    # tell the input stream where to send its data
    for stream in upstreams:
        input_stream.connect(stream)

    try:
        # start the input stream
        await input_stream.start()
    except CancelledError as e:
        await input_stream.close()
        await output_stream.close()
        print("\n")
    except DataStreamInterrupted:
        await output_stream.close()
        print("\n")


def find_interface():
    print("Searching for interface(s)...")
    modems = [filename for filename in os.listdir('/dev/') if filename.startswith('tty.usbmodem')]

    if not modems:
        print("no interfaces found.")
        return

    for num, modem in enumerate(modems):
        print(f"[{num}] /dev/{modem}")
    
    if modem:
        return f"/dev/{modem}"


def find_device(interface):
    muses = list_muses(backend='bgapi', interface=interface)
    return muses

def main():
    parser = argparse.ArgumentParser(
        description='example to stream data',
    )

    parser.add_argument('-d', '--downsample_scale', type=int, help="number of samples to average across = ex. 256 averages all samples in a second")
    parser.add_argument('-s', '--sample_rate', type=int, help="sample rate of device in Hz - usually 256Hz")
    parser.add_argument('--find-interface', action='store_true', help="locate the bluetooth dongle")
    parser.add_argument('--find-device', action='store_true', help='locate the name of the muse device')
    parser.add_argument('--interface', type=str, help="device location for the usb bluetooth")
    parser.add_argument('--address', type=str, help="mac address of the muse device. eg. 00:11:22:AA:BB:CC")
    parser.add_argument('--device-name', type=str, help="name of the muse device. eg. Muse-ABC1")
    parser.add_argument('--EZ', action='store_true', help="Attempt Automatic start.  Ensure Muse is on and BLED112 is connected.")
    parser.add_argument('--file', type=str, help="record raw eeg output directly to file")
    parser.add_argument('--osc', action='store_true', help="send muse output to osc")
    
    args = parser.parse_args()

    osc_port = None
    if args.osc:
        osc_port = 9807
    
    if args.EZ:
        args.interface = find_interface()
        muses = find_device(args.interface)
        if len(muses) < 1:
            print('no muse devices available')
            exit(1)
        args.address = muses[0]['address']
        args.device_name = muses[0]['name']
        if not args.sample_rate:
            args.sample_rate = 256
    elif args.find_interface:
        find_interface()
    elif args.find_device:
        if not args.interface:
            print("interface must be specified")
            return
        find_device(args.interface)
    else:
        if not args.address or not args.device_name or not args.interface:
            print("`--address`, `--device-name` and `--interface` must be specified")
            return
    try:
        event_loop.run_until_complete(
            muse_streamer(args.sample_rate,
                          args.address, args.device_name,
                          args.interface, args.downsample_scale, args.file,
                          osc_port))
    except KeyboardInterrupt:
        all_tasks = asyncio.gather(*asyncio.all_tasks(event_loop), return_exceptions=True)
        all_tasks.add_done_callback(lambda t: event_loop.stop())
        all_tasks.cancel()

        # Keep the event loop running until it is either destroyed or all
        # tasks have really terminated
        while not all_tasks.done() and not event_loop.is_closed():
            event_loop.run_forever()


if __name__ == '__main__':
    main()
