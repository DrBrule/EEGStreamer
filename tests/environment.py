import asyncio
import os
import time
from behave import use_step_matcher
from behave.api.async_step import async_run_until_complete
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

use_step_matcher("re")

TMP_DIR = "/tmp/eegstreamer"


def before_all(context):
    # make sure the tmp directory exists
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    # create a temp path for this run
    epoch_time = int(time.time())
    context.tmp_path = f"/tmp/eegstreamer/{epoch_time}"
    os.makedirs(context.tmp_path)


def after_all(context):
    pass


@async_run_until_complete
async def before_scenario(context, feature):

    if 'osc' in feature.tags:
        context.osc_samples = list()
        context.osc_address = {}

        def filter_handler(address, *args):
            context.osc_samples.append(args)

        def default_handler(address, *args):
            if address not in context.osc_address:
                context.osc_address[address] = []
            context.osc_address[address].append(args)

        dispatcher = Dispatcher()
        dispatcher.map("/eeg", filter_handler)
        dispatcher.set_default_handler(default_handler)

        context.osc_server = AsyncIOOSCUDPServer(('127.0.0.1', 1337), dispatcher, asyncio.get_event_loop())
        context.transport, context.protocol = await context.osc_server.create_serve_endpoint()

    await asyncio.sleep(0)


def after_scenario(context, feature):

    if 'osc' in feature.tags:
        context.transport.close()
