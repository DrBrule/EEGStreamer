import time

from behave import *
from behave.api.async_step import async_run_until_complete


@when(r"the stream runs for (?P<duration>\d+)\s*seconds")
@async_run_until_complete
async def step_impl(context, duration):
    context.start_time = time.time_ns()
    await context.start_stream.start(duration=int(duration))
