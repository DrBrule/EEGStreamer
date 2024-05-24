import os, csv, json
from logging import getLogger

import pandas as pd
import numpy as np
# import mne, sklearn
# not needed yet
import math, time
from random import random
import scipy
from scipy import signal
from scipy.signal import butter, sosfilt
from scipy.integrate import simps
from pprint import pprint as pp
from collections import OrderedDict

logger = getLogger(__name__)


def uShapeDistribution( value ):
    if value <= .2:
        value = value * random()
    elif .2  < value <= .65:
        value = value * random() * random()
    elif .65 < value <= .8:
        value = (value / random()) / random()
    else:
        value = value / random()
    if value > 1:
        value = 1
    return value
    

def ScaleOutput( in_data ):
    proc_data   = []
    out_data    = []
    mean        = np.mean(in_data)
    stdev       = np.std(in_data)
    for item in in_data:
        proc_data.append( abs( ( item - mean ) / stdev*stdev ) )
    if max(proc_data) > 1:
        for item in proc_data:
            item    = item / max(proc_data)
            out_data.append(item)
    else:
        out_data = proc_data
    return out_data


def PhaseCoherence( freq , timeSeries , sample_rate=256 ):
    """given a set of 
    
    """
    # Get parameters of input data
    nMeasures   = np.shape( timeSeries )[0]
    nSamples 	= np.shape( timeSeries )[1]
    nSecs       = nSamples / sample_rate
    
    # Calculate FFT for each measurement (spect is freq x measurements)
    spectrogram = np.fft.fft( timeSeries , axis=1 )
    
    # Normalise by amplitude
    spectrogram = spectrogram / abs( spectrogram )
    
    # Find spectrum values for frequency bin of interest
    freqRes = 1 / nSecs;
    foibin = round(freq / freqRes + 1) - 1
    spectrogramFoi = spectrogram[:,foibin]
    
    # Find individual phase angles per measurement at frequency of interest
    anglesFoi = np.arctan2(spectrogramFoi.imag, spectrogramFoi.real)
    
    # PC is root mean square of the sums of the cosines and sines of the angles
    PC = np.sqrt((np.sum(np.cos(anglesFoi)))**2 + (np.sum(np.sin(anglesFoi)))**2) / np.shape(anglesFoi)[0]
    
    # Print the value
    # logger.debug('----------------------------------');
    # logger.debug('Phase coherence value = ' + str("{0:.3f}".format(PC)));
    return PC


def bandpower_simple(x, fs, fmin, fmax):
    f, Pxx = scipy.signal.periodogram(x, fs=fs)
    ind_min = scipy.argmax(f > fmin) - 1
    ind_max = scipy.argmax(f > fmax) - 1
    return scipy.trapz( Pxx[ind_min: ind_max] , f[ind_min: ind_max])


def bandpower_complex( data , sample_rate=256 , band=[0,40] , window_sec=None , relative=False):
    """Compute the average power of the signal x in a specific frequency band.
    
    Parameters
    ----------
    data : 1d-array
        Input signal in the time-domain.
    sample_rate : float
        Sampling frequency of the data.
    band : list
        Lower and upper frequencies of the band of interest.
    window_sec : float
        Length of each window in seconds.
        If None, window_sec = (1 / min(band)) * 2
    relative : boolean
        If True, return the relative power (= divided by the total power of the signal).
        If False (default), return the absolute power.
    
    Return
    ------
    bp : float
        Absolute or relative band power.
    """
    from scipy.signal import welch
    from scipy.integrate import simps
    
    band = np.asarray(band)
    low, high = band
    
    # Define window length
    if window_sec is not None:
        nperseg = window_sec * sample_rate
    else:
        nperseg = (2 / low) * sample_rate

    # Compute the modified periodogram (Welch)
    freqs, psd = welch(data, sample_rate, nperseg=nperseg)
    
    # Frequency resolution
    freq_res = freqs[1] - freqs[0]
    logger.debug(freq_res)
    # Find closest indices of band in frequency vector
    idx_band = np.logical_and(freqs >= low, freqs <= high)
    logger.debug(idx_band)
    
    # Integral approximation of the spectrum using Simpson's rule.
    bp = simps(psd[idx_band], dx=freq_res)
    
    if relative:
        bp /= simps(psd, dx=freq_res)
    return bp


def analyzeEEG( data=np.random.rand(2560,5)*1000 , device='muse', sample_rate = 256):
    '''
    Parameters
    -----------
    data 
        the data packet of incoming raw EEG.  
        If it's not defined, then throw out a random chunk of 'voltages'
    device
        which EEG device is being used.  
        This will have implications for how the analyses get run, but for now, assume Muse 2
    sample_rate
        the sampling rate in Hz of the device being used.  
        256Hz is the standard
    
    analyzeEEG runs the core analyses on the incoming data.
    It outputs a dictionary with all the various PSD, coherences, and a few ratios for the time chunk
     
    Once we have a good training dataset for meditation states,
    we can incorporate a classification step in here based on a trained model (done elsewhere) with model.fit()
    '''
    if device=='muse':
        electrodes = ["TP9",  "AF7", "AF8" , "TP10"]
    
    # first detrend the data
    window_len  = data.shape[0] / sample_rate
    detrended   = scipy.signal.detrend( data )
    
    # now filter the data from .1 - 40 Hz using a butterworth bandpass filter 
    low         = 1  / ( sample_rate / 2 )
    high        = 40 / ( sample_rate / 2 )
    order       = 12      # 12dB / octave
    sos         = butter(order, [low, high], btype='bandpass', output='sos')
    filtered    = sosfilt(sos, detrended)
    # now calculate frontal coherence for the relevant frequencies (i.e. 0.1 - 40 Hz)
    f, frontal_coherence    = scipy.signal.coherence(filtered[:,1], filtered[:,2], fs=sample_rate, nperseg=sample_rate*1, window='hann', detrend=False)    
    # now calculate average coherence for each f
    # calculate average frontal coherence for each frequency band relative to all coherence values 
    eeg_bands = {'Delta': (1, 4),
                 'Theta': (4, 8),
                 'Alpha': (8, 12),
                 'Beta' : (12, 24),
                 'Gamma': (24, 48) }
    
    coherence = OrderedDict()
    for band in eeg_bands:
        coherence[band] = 0
        for freq in range( *eeg_bands[band] ):
            coherence[band] += ( frontal_coherence[freq] - min( frontal_coherence ) ) / ( max( frontal_coherence ) - min( frontal_coherence ) )
        coherence[band] = coherence[band] / len( range( *eeg_bands[band] ) )
    
    ####   
    ## populate a dictionary with relative power
    ## for each frequency band across all electrodes
    #### this whole section can be re-written better
    power = {}
    for electrode in electrodes:
        # set up dict
        power[electrode] = OrderedDict()
        # now evaluate band power over the meditation session 
        tmp = data[ : , electrodes.index(electrode) ]
        # we can cut this up more this week
        for band in eeg_bands:
            freq_range  = [ eeg_bands[band][0] , eeg_bands[band][1] ]
            power[electrode][band] = bandpower_simple( tmp , sample_rate , eeg_bands[band][0] , eeg_bands[band][1] )
            # power[electrode][band] = bandpower( data , sample_rate , freq_range , window_sec = 1 , relative=False)
    
    ####
    
    total_power = OrderedDict()
    for band in eeg_bands:
        total_power[band] = 0
    
    # 5 electrodes i guess ?
    for electrode in electrodes: 
        for band in eeg_bands:
            total_power[band] += ( power[electrode][band] / 5 )
    
    # now normalize to octave width because each band is different 
    # is this necessary ? 
    octaves = {'Delta':4, 'Theta':1, 'Alpha':.5 , 'Beta':1, 'Gamma':1}
    power_array = []
    
    for band in eeg_bands:
        total_power[band] = total_power[band]  / octaves[band]
        power_array.append( total_power[band] )
    
    # scaled to get relative power in each band 
    scaled_power = {}
    for band in eeg_bands:
        scaled_power[band]  = ( total_power[band] / ( sum( power_array ) ) )
    
    # calculate some other interesting things about the brain data 
    # this could be done later on in the pipeline, but it's fun to have here 
    # as there is a specific reason to collect this data
    
    # Higher Delta / Beta suggests anxiety
    delta_beta_ratio    = scaled_power['Delta'] / scaled_power['Beta'] 
    
    # Higher Alpha / Gamma suggests calm / relaxed 
    alpha_gamma_ratio   = scaled_power['Alpha'] / scaled_power['Gamma']
    
    power_band          = max( scaled_power , key=scaled_power.get )
    coherence_channel   = max( coherence , key=coherence.get )
    coherence_freq      = np.where(frontal_coherence[0:40] == max(frontal_coherence[0:40]))[0][0]
    frontal_coherence   = np.mean(frontal_coherence)
    
    analysis = OrderedDict()
    analysis = {
    'Delta Power'       : scaled_power['Delta'],
    'Theta Power'       : scaled_power['Theta'],
    'Alpha Power'       : scaled_power['Alpha'],
    'Beta Power'        : scaled_power['Beta'],
    'Gamma Power'       : scaled_power['Gamma'], 
    'Delta Coherence'   : coherence['Delta'],
    'Theta Coherence'   : coherence['Theta'], 
    'Alpha Coherence'   : coherence['Alpha'],
    'Beta Coherence'    : coherence['Beta'],
    'Gamma Coherence'   : coherence['Gamma'],
    'Ratio Delta-Beta'  : delta_beta_ratio,
    'Ratio Alpha-Gamma' : alpha_gamma_ratio,
    'Frontal Coherence' : frontal_coherence,
    'Coherence Band'    : coherence_channel,
    'Coherence Frequency': coherence_freq,
    'Power Band'        : power_band,
    'Coherence Frequency': int(coherence_freq)  # pyosc doesn't recognize numpy's int64
    }
    return analysis