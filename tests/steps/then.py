import time
from math import floor

from behave import *
from behave.api.async_step import async_run_until_complete
from hamcrest import assert_that, equal_to, is_ as has_, has_key

from tests.matchers import channel_count_of, duration_of, has_address


@then(r"(?P<sample_count>\d+) samples are received")
def step_impl(context, sample_count: str):
    assert_that(context.output_stream.sample_count(), equal_to(int(sample_count)), "samples")


@then(r"the file has (?P<line_count>\d+) lines")
@async_run_until_complete
async def step_impl(context, line_count):
    await context.output_stream.close()
    lines = 0
    with open(context.filename) as file:
        for _ in file.readlines():
            lines += 1
    assert_that(lines, equal_to(int(line_count)), "for file '{}'".format(context.filename))


@then(r"(?P<sample_count>\d+) samples are received via OSC(?: on (?P<address>.+?) address)?")
@async_run_until_complete
async def step_impl(context, sample_count, address):
    if address:
        assert_that(context.osc_address, has_address(address))
        assert_that(len(context.osc_address[address]), equal_to(int(sample_count)))
    else:
        assert_that(len(context.osc_samples), equal_to(int(sample_count)))


@then(r"each sample has (?P<channel_count>\d+) data channels")
@async_run_until_complete
async def step_impl(context, channel_count):
    for sample in context.osc_samples:
        assert_that(len(sample), equal_to(int(channel_count)))


@then(r"OSC will receive (?P<channel_count>\d+) data channels")
@async_run_until_complete
async def step_impl(context, channel_count):
    assert_that(list(context.osc_address.keys()), has_(channel_count_of(int(channel_count))))


@then(r"(?P<run_time>\d+) (?P<units>seconds|milliseconds|nanoseconds) have elapsed")
@async_run_until_complete
async def step_impl(context, run_time, units):
    correction = 1  # time is recorded in nanoseconds
    if units == 'seconds':
        correction = 1e9
    elif units == 'milliseconds':
        correction = 1e6

    actual = (time.time_ns() - context.start_time) / correction
    assert_that(floor(actual), has_(duration_of(int(run_time))))
