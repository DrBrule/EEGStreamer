Feature: Streaming to an OSC output

  @osc
  Scenario: Random stream to OSC output
    Given a random eeg input stream of 10 HZ
      And the output is sent via OSC
    When the stream runs for 2 seconds
    Then 20 samples are received via OSC

  @osc
  Scenario: Random stream to OSC output
    Given a random eeg input stream of 20 HZ with 3 channels
      And the output is sent via OSC
    When the stream runs for 2 seconds
    Then 40 samples are received via OSC
      And OSC will receive 3 data channels

  @osc
  Scenario: Muse device stream to OSC output
    Given a Muse device sends a simulated stream of data
      And the output is sent via OSC
    When the stream runs for 2 seconds
    Then 512 samples are received via OSC

  @osc
  Scenario: Muse device stream multiple channels
    Given a Muse device sends a simulated stream of data
      And the output is sent via OSC
    When the stream runs for 2 seconds
    Then OSC will receive 5 data channels

  @osc
  Scenario: random stream on multiple addresses
    Given a random eeg input stream of 20 HZ with 3 channels
    And the output is sent via OSC on /tmp address
    And the output is sent via OSC on /test address
    When the stream runs for 2 seconds
    Then 40 samples are received via OSC on /tmp address
      And 40 samples are received via OSC on /test address
