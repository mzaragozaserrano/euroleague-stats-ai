Feature: Persistence & UX Enhancements
  As a user
  I want persistent chat history and improved UX
  So that I can have a seamless conversation experience

  Scenario: Chat history persists across page reloads
    Given I have started a chat session
    When I send a message "Cuantos puntos tiene Larkin?"
    And the assistant responds with data
    And I refresh the page
    Then the message history should still be visible
    And the localStorage should contain the messages

  Scenario: Clear history functionality works correctly
    Given I have multiple messages in my chat history
    When I click the clear history button
    And I confirm the clearing action
    Then all messages should be removed
    And the chat history should be empty
    And localStorage should be cleared

  Scenario: Clear history is not available when there are no messages
    Given I start a fresh chat session
    And I have no messages in my history
    Then the clear history button should not be visible

  Scenario: Cold start warning appears and can be dismissed
    Given I am sending my first query
    When the request takes longer than 3 seconds
    Then a cold start warning should be displayed
    And I should be able to dismiss the warning with a button
    And the warning should disappear from the UI

  Scenario: Rate limit warning prevents further queries
    Given I have reached the 50 queries per day limit
    When I try to send a new message
    Then a rate limit warning should be displayed
    And the send button should be disabled
    And the input field should be disabled

  Scenario: Rate limit warning can be dismissed
    Given a rate limit warning is displayed
    When I click the dismiss button on the warning
    Then the warning should disappear
    And the UI should close the warning banner

  Scenario: Debounce prevents multiple rapid submissions
    Given the chat input is active
    When I send multiple messages in rapid succession
    Then only the last message should be submitted
    And the debounce delay (300ms) should be respected

  Scenario: Input field auto-resizes as user types
    Given I focus on the chat input
    When I type a long message with multiple lines
    Then the textarea should expand to show all text
    And the height should not exceed 120px max

  Scenario: Message count is tracked in chat store metadata
    Given I start a chat session
    When I send multiple queries
    Then the total queries count should increment
    And the metadata should reflect the correct message count

  Scenario: Chat state persists with version migration
    Given I have chat storage with v1 format
    When the app loads with v2 persistence
    Then the migration should handle the version upgrade
    And the old messages should still be accessible
    And new fields should have default values

  Scenario: Last cleared timestamp is tracked
    Given I have chat history
    When I clear the chat history
    Then the lastCleared timestamp should be recorded
    And future page reloads should not restore cleared history

  Scenario: Warning dismissal is immediate without persisting
    Given I have a cold start or rate limit warning
    When I dismiss the warning
    Then the warning state should reset immediately
    And it should not persist to localStorage
    And a new query might show the warning again if conditions are met

