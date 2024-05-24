from behave import *
from eegstreamer.transforms import ConstantFactorEEGTransformer, DownSampleEEGTransformer, PowerCoherenceEEGTransformer


@given(r"the constant transformer is applied")
def step_impl(context):
    transformer = ConstantFactorEEGTransformer(factor=2)
    context.upstream.connect(transformer)
    context.upstream = transformer

@given(r"the downsample transformer is applied")
def step_impl(context):
    transformer = DownSampleEEGTransformer()
    context.upstream.connect(transformer)
    context.upstream = transformer

@given(r"the PowerCoherence transformer is applied")
def step_impl(context):
    transformer = PowerCoherenceEEGTransformer()
    context.upstream.connect(transformer)
    context.upstream = transformer
