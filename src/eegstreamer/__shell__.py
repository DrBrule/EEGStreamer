import argparse

from eegstreamer.inputs import FakeEEGDeviceInputStreamer
from eegstreamer.outputs import ScreenEEGOutputStreamer, OscOutputStreamer
from eegstreamer.transforms import PowerCoherenceEEGTransformer, DownSampleEEGTransformer
import asyncio


async def streamer(sample_rate):
    if not sample_rate:
        sample_rate = 256
    # create the output stream
    screen_stream = ScreenEEGOutputStreamer()
    pct_out_stream = OscOutputStreamer(address='/pct', port=9807)
    eeg_out_stream = OscOutputStreamer(address='/eeg', port=9807)

    pct_stream = PowerCoherenceEEGTransformer()
    # pct_stream.connect(screen_stream)
    pct_stream.connect(pct_out_stream)

    ds32_stream = DownSampleEEGTransformer(sample_rate=32)
    ds32_stream.connect(eeg_out_stream)
    ds32_stream.connect(screen_stream)

    input_stream = FakeEEGDeviceInputStreamer(device='muse')
    input_stream.connect(pct_stream)
    input_stream.connect(ds32_stream)

    await input_stream.start()


def main():
    parser = argparse.ArgumentParser(
        description='example to stream data',
    )

    parser.add_argument('-s', '--sample-rate', type=int, help="down-sample rate")

    args = parser.parse_args()

    asyncio.run(streamer(args.sample_rate))


if __name__ == '__main__':
    main()
