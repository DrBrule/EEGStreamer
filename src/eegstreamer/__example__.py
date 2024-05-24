import argparse

from eegstreamer.inputs import FakeEEGDeviceInputStreamer
from eegstreamer.outputs import ScreenEEGOutputStreamer, JSONFileOutputStreamer
from eegstreamer.transforms import DownSampleEEGTransformer, PowerCoherenceEEGTransformer
import asyncio


async def streamer(sample_rate):

    if not sample_rate:
        sample_rate = 256
    # create the output stream
    output_stream = JSONFileOutputStreamer('dual.eeg')
    
    # create the stream to transform the data
    pct_stream = PowerCoherenceEEGTransformer()
    # tell the transform stream where to send its data
    pct_stream.connect(output_stream)

    # create the input stream
    input_stream = FakeEEGDeviceInputStreamer(device='muse')
    # tell the input stream where to send its data
    input_stream.connect(output_stream)
    input_stream.connect(pct_stream)

    # start the input stream
    await input_stream.start(duration=10)


def main():

    parser = argparse.ArgumentParser(
        description='example to stream data',
    )

    parser.add_argument('-s', '--sample-rate', type=int, help="down-sample rate")

    args = parser.parse_args()

    asyncio.run(streamer(args.sample_rate))


if __name__== '__main__':
    main()
