from abc import ABC, abstractmethod
from logging import getLogger
from typing import Union

from stringcase import snakecase

from eegstreamer import PowerCoherenceException
from eegstreamer.data import EEGData
from eegstreamer.outputs import EEGOutputStreamer

import eegstreamer.eeg_analysis as eeg

import numpy as np
import time

logger = getLogger(__name__)



class EEGTransformer(ABC):

    def __init__(self):
        self.outputs = []

    def connect(self, stream: Union[EEGOutputStreamer]):
        self.outputs.append(stream)

    async def send(self, data) -> None:
        for output in self.outputs:
            await output.receive(data)

    @abstractmethod
    async def receive(self, data: EEGData) -> None:
        pass


class ConstantFactorEEGTransformer(EEGTransformer):

    def __init__(self, factor: int):
        super().__init__()
        self.factor = factor

    async def receive(self, data: EEGData) -> None:

        packet = data['packet']
        new_packet = []
        for v in packet:
            new_packet.append(v * self.factor)
        await self.send(data)


class DownSampleEEGTransformer(EEGTransformer):
    '''
    Simply cuts incoming data from 256Hz to 1Hz
    '''
    def __init__(self, downsample_scale: int = 256, sample_rate: int = 256):
        super().__init__()
        self.downsample_scale = downsample_scale
        self.sample_rate = sample_rate
        # TODO: number of channels needs to be configurable based on device
        self.packet_buffer = np.zeros((1, 4))
        self.channel_buffer = {}

    async def receive(self,  data: EEGData) -> None:

        # accrue y samples of data for analysis
        if self.packet_buffer.shape[0] < self.sample_rate:
            for channel, value in data.items():
                if channel == 'packet':
                    self.packet_buffer = np.append(self.packet_buffer, [value], axis=0)
                else:
                    if channel not in self.channel_buffer:
                        self.channel_buffer[channel] = []
                    self.channel_buffer[channel].append(value)
        elif self.packet_buffer.shape[0] >= self.sample_rate:
            out_data = {channel: sum(values)/len(values) for channel, values in self.channel_buffer.items()}
            out_data['packet'] = np.average(self.packet_buffer, axis=0)

            # TODO: number of channels needs to be configurable based on device
            self.packet_buffer = np.zeros((1, 4))
            self.channel_buffer = {}
            
            await self.send(EEGData(out_data))



class PowerCoherenceEEGTransformer( EEGTransformer ):
    '''
    This transformer runs an analysis on two timescales :
    Each anaylsis consists of :
     
        PSD bandpower analysis
        Coherence by band
        ð/β ratio
        α/γ ratio
        Frontal Coherence
    
    Accrue data 
    because there may be a lag in data analysis, 
    reduce the amount of analyses done, but make them more frequent
    increment long_buffer every 64Hz
    analyze the long_buffer data (tentatively, 1 second)
    then analyze the long_buffer data (tentatively, 10 seconds)
    then combine the two so that the user can 'move the needle'
    '''
    
    def __init__(self, sample_rate: int = 256, *args, **kwargs):
        '''
        initial data is a [0,0,0,0,0] for short_buffer
        and 10 seconds of simulated EEG for the long_buffer 
        assumes that device is Muse (i.e. 5 channels, 256Hz etc)
        '''
        super().__init__()
        self.sample_rate        = int( sample_rate )
        self.window_length      = 5
        self.short_buffer_size  = int( self.sample_rate / 4 )
        self.long_buffer_size   = self.sample_rate * self.window_length
        self.short_buffer       = np.random.rand( 1 , 4) * 1000
        self.long_buffer        = np.random.rand( int( self.sample_rate * self.window_length) , 4 ) * 1000
        # for counting times of loops...collection slows down over time
        self.start_time         = time.time()
        self.num_analyses       = 0
        self.average_time       = 0
        self.time_elapsed       = [0.25]
        self.latest             = time.time()
        self.last               = 0

    async def receive(self,  data: EEGData) -> None:
        
        # accrue 1 second of data for analysis
        packet = data['packet']
        if  self.short_buffer.shape[0] < ( self.short_buffer_size ): 
            #accrue data for x amount of time (1 second currently)
            self.short_buffer = np.vstack( ( self.short_buffer , [packet] ) )
            
        elif  self.short_buffer.shape[0] >= ( self.short_buffer_size ) :
            if self.num_analyses == 0 :
                self.start_time = time.time()
                self.latest = time.time() - self.start_time
            else:
                self.latest = ( time.time() - self.start_time ) / self.num_analyses
                self.time_elapsed.append( self.latest )
                self.average_time = np.mean( self.time_elapsed )
                logger.debug(str(self.average_time))
            
            self.num_analyses += 1
            
            # clear earliest X samples from long_buffer, then tack on latest X samples
            # so that we have shifted the window but maintained the length
            self.long_buffer = self.long_buffer[ self.short_buffer_size: , : ]
            self.long_buffer = np.vstack( (self.long_buffer, self.short_buffer) )
            analysis   = eeg.analyzeEEG( data=self.long_buffer  , device='muse', sample_rate = self.sample_rate)
            
            self.short_buffer = self.short_buffer[255:,:] # np.array( [packet] )
                
            # sum the analyses and scale ? or can do later on
            out_data = {snakecase(k): v for k, v in analysis.items()}
            out_data['packet'] = list(analysis.values())
            output = EEGData(out_data)
            # reset short_buffer
            await self.send( output )
         
    