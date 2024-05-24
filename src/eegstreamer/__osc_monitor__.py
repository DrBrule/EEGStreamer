import argparse
import asyncio
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher

from eegstreamer.inputs import FakeEEGDeviceInputStreamer
from eegstreamer.outputs import OscOutputStreamer


async def sender(ip='127.0.0.1', port=1337):

    output_stream = OscOutputStreamer()

    input_stream = FakeEEGDeviceInputStreamer(sample_rate=256, device='muse')
    input_stream.connect(output_stream)

    await input_stream.start()


def eeg_packet_handler(address, *args):
    print(f"{address}: {args}")


def eeg_channel_handler(address, *args):
    print(f"{address}: {args}")


def default_handler(address, *args):
    print(f"default ({address}): {args}")


dispatcher = Dispatcher()
dispatcher.map("/eeg", eeg_packet_handler)
dispatcher.map("/eeg/*", eeg_channel_handler)
dispatcher.set_default_handler(default_handler)

event_loop = asyncio.get_event_loop()

async def loop():
    while True:
        await asyncio.sleep(1)


async def receiver(ip='127.0.0.1', port=1337):
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, event_loop)
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    print(f"server listening on {ip}:{port}")
    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


def main():
    parser = argparse.ArgumentParser(
        description='Performs some useful work.',
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--send', action='store_true', help="send EEG data via OSC")
    group.add_argument('--receive', action='store_true', help="receive EEG data via OSC")
    parser.add_argument('--ip', type=str, help='address to send/receive data on (default: 127.0.0.1)', default='127.0.0.1')
    parser.add_argument('--port', type=int, help="port to send/receive data on (default: 1337)", default=1337)



    args = parser.parse_args()

    if args.receive:
        event_loop.run_until_complete(receiver(ip=args.ip, port=args.port))
    elif args.send:
        event_loop.run_until_complete(sender(port=args.port))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

