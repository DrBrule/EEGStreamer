Feature: Streaming to screen

  Scenario: Writing a random eeg stream of 100 samples to the screen
    Given a random eeg input stream of 10 HZ
      And the output is the screen
    When the stream runs for 10 seconds
    Then 100 samples are received

  Scenario: Writing a random eeg stream of 500 samples to the screen
    Given a random eeg input stream of 20HZ
      And the output is the screen
    When the stream runs for 10 seconds
    Then 200 samples are received

  Scenario: Receiving data from a (fake) muse device
    Given a Muse device sends a simulated stream of data
      And the output is the screen
    When the stream runs for 10 seconds
    Then 2560 samples are received

  @current
  Scenario: Receiving data and transforming device data
    Given a random eeg input stream of 20 HZ
      And the constant transformer is applied
      And the output is the screen
    When the stream runs for 2 seconds
    Then 40 samples are received
      And 2 seconds have elapsed

  @downsample
  Scenario: Receiving data and downsampling device data
    Given a Muse device sends a simulated stream of data
      And the downsample transformer is applied
      And the output is the screen
    When the stream runs for 2 seconds
    Then 2 samples are received
    
  @PowerCoherence
  Scenario: Receiving data and analyzing for Power and Coherence data
    Given a Muse device sends a simulated stream of data
      And the PowerCoherence transformer is applied
      And the output is the screen
    When the stream runs for 2 seconds
    Then 7 samples are received



