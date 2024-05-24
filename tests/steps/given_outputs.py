import os
from behave import *

from eegstreamer.outputs import JSONFileOutputStreamer, ScreenEEGOutputStreamer, OscOutputStreamer, \
    CSVFileOutputStreamer


@given(r"the output (?P<file_type>json|csv) file has a name of (?P<filename>.+?)")
def step_impl(context, file_type, filename):
    context.filename = os.path.join(context.tmp_path, filename)
    if file_type == 'json':
        context.output_stream = JSONFileOutputStreamer(context.filename)
    else:
        context.output_stream = CSVFileOutputStreamer(context.filename)
    context.upstream.connect(context.output_stream)


@given(r"the output is the screen")
def step_impl(context):
    context.output_stream = ScreenEEGOutputStreamer()
    context.upstream.connect(context.output_stream)


@given(r"the output is sent via OSC(?: on (?P<address>.+?) address)?")
def step_impl(context, address):
    params = {}
    if address:
        params = {
            'address':address
        }
    context.output_stream = OscOutputStreamer(**params)
    context.upstream.connect(context.output_stream)
