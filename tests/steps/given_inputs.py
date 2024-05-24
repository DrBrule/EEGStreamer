from pathlib import Path

from behave import *
import os.path

from eegstreamer.inputs import RandomEEGInputStream, FakeEEGDeviceInputStreamer, FileEEGInputStreamer, \
    JSONFileInputStreamer, CSVFileInputStreamer


# @given("the input file {eeg_filename}")
# def step_impl(context, eeg_filename):
#     assert os.path.exists(eeg_filename)
#     context.file_name = eeg_filename


@given(r"a random eeg input stream of (?P<frequency>\d+)\s*HZ((?:\s*with) (?P<channel_count>\d+) (?:channels))?")
def step_impl(context, *args, **kwargs):
    params = { 'sample_rate': int(kwargs['frequency']) }
    if 'channel_count' in kwargs and kwargs['channel_count']:
        params['channel_count'] = int(kwargs['channel_count'])
    context.start_stream = RandomEEGInputStream(**params)
    context.upstream = context.start_stream


@given(r"a Muse device sends a simulated stream of data")
def step_impl(context):
    context.start_stream = FakeEEGDeviceInputStreamer(device='muse')
    context.upstream = context.start_stream


@given(r"an input (?P<file_type>json|csv) file having a name of (?P<filename>.+?)")
def step_impl(context, file_type, filename):
    path = Path(__file__).parent.parent
    fp = os.path.join(path, 'fixtures', filename)
    if file_type == 'json':
        context.start_stream = JSONFileInputStreamer(fp)
    else:
        context.start_stream = CSVFileInputStreamer(fp)
    context.upstream = context.start_stream

# @when("the file is opened")
# def step_impl(context):
#     context.file_handle = open(context.file_name, 'r')
#
#
# @then("an eeg input stream is created")
# def step_impl(context):
#     EEGFileInputStreamer(context.file_handle)

