Feature: Streaming to file

  @file
  Scenario: Writing a random eeg stream of 500 samples to a file
    Given a random eeg input stream of 100HZ
      And the output file has a name of output.eeg
    When the stream runs for 5 seconds
    Then the file has 500 lines

    @file
    Scenario: Muse emulator and transformer to file
     Given a Muse device sends a simulated stream of data
      And the PowerCoherence transformer is applied
      And the output json file has a name of muse_transform_file_json.eeg
    When the stream runs for 5 seconds
    Then the file has 5 lines

    @file
    Scenario: Muse emulator to json file
     Given a Muse device sends a simulated stream of data
      And the output json file has a name of muse_to_file_json.eeg
    When the stream runs for 5 seconds
    Then the file has 1280 lines

    @osc
    Scenario: Read from json file and send to OSC
      Given an input json file having a name of muse_json_data.eeg
        And the output is sent via OSC
      When the stream runs for 0 seconds
      Then 1280 samples are received via OSC

    @file
    Scenario: Muse emulator to csv file
     Given a Muse device sends a simulated stream of data
      And the output csv file has a name of muse_to_file_csv.eeg
    When the stream runs for 5 seconds
    Then the file has 1281 lines

    @osc
    Scenario: Read from csv file and send to OSC
      Given an input csv file having a name of muse_csv_data.eeg
        And the output is sent via OSC
      When the stream runs for 0 seconds
      Then 1280 samples are received via OSC