Feature: Chat Store Management
  As a frontend developer
  I want a Zustand store to manage chat state
  So that messages, history, and loading states are properly synchronized

  Scenario: Store initializes with empty state
    Given the chat store is created
    Then the messages array should be empty
    And the history array should be empty
    And isLoading should be false
    And error should be null

  Scenario: Adding a message to the store
    Given the chat store is created
    When I add a message with role "user" and content "Hello"
    Then the messages array should contain 1 message
    And the history array should contain 1 message
    And the message role should be "user"
    And the message content should be "Hello"

  Scenario: Setting loading state
    Given the chat store is created
    When I set loading to true
    Then isLoading should be true
    And error should be null

  Scenario: Setting and clearing error
    Given the chat store is created
    When I set error to "Network error"
    Then error should be "Network error"
    And isLoading should be false
    When I clear error
    Then error should be null

  Scenario: Chat history persists in localStorage
    Given the chat store is created
    And I add a message with role "user" and content "Test message"
    When the store is rehydrated from localStorage
    Then the messages array should contain 1 message
    And the message content should be "Test message"

  Scenario: Clear history action removes all messages
    Given the chat store is created
    And I add a message with role "user" and content "Message 1"
    And I add a message with role "assistant" and content "Response 1"
    When I clear history
    Then the messages array should be empty
    And the history array should be empty
    And error should be null

  Scenario: Cold start warning is displayed
    Given the chat store is created
    When I set cold start warning to true
    Then coldStartWarning should be true

  Scenario: Rate limit warning is displayed
    Given the chat store is created
    When I set rate limit warning to true
    Then rateLimitWarning should be true

  Scenario: Message count is calculated correctly
    Given the chat store is created
    And I add a message with role "user" and content "Message 1"
    And I add a message with role "assistant" and content "Response 1"
    And I add a message with role "user" and content "Message 2"
    When I get message count
    Then message count should be 3

  Scenario: Multiple messages with metadata
    Given the chat store is created
    When I add a message with role "assistant" and SQL query metadata
    Then the messages array should contain 1 message
    And the message should have SQL query data
    And the message should have visualization type "bar"



