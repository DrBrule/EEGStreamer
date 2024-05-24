from hamcrest.core.base_matcher import BaseMatcher


class HasChannelCountOf(BaseMatcher):

    def __init__(self, channel_count):
        self.channel_count = channel_count

    def _matches(self, item):
        return len(item) == self.channel_count

    def describe_to(self, description):
        description.append_text(f"number of channels to be {self.channel_count}")


def channel_count_of(channel_count):
    return HasChannelCountOf(channel_count)


class HasDurationOf(BaseMatcher):

    def __init__(self, run_time):
        self.run_time = run_time

    def _matches(self, item):
        return item == self.run_time

    def describe_to(self, description):
        description.append_text(f"run time of {self.run_time}")


def duration_of(run_time):
    return HasDurationOf(run_time)


class HasAddress(BaseMatcher):

    def __init__(self, address):
        self.address = address

    def _matches(self, item):
        return self.address in item

    def describe_to(self, description):
        description.append_text(f"an address of : {self.address}")

    def describe_mismatch(self, item, mismatch_description):
        mismatch_description.append_text("only has addresses").append_description_of(list(item.keys()))


def has_address(address):
    return HasAddress(address)
