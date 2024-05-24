Feature: Testing scenarios for the Power Coherence Transformer

  @bug
  Scenario: Power Coherence Transformer with random data
    Given a random eeg input stream of 256 HZ with 5 channels
      And the PowerCoherence transformer is applied
      And the output is the screen
    When the stream runs for 10 seconds
    Then 10 seconds have elapsed
      And 2560 samples are received
