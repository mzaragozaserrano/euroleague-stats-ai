Feature: Natural Language Response
  As a user
  I want the system to provide a natural language answer explaining the data
  So that I can understand the results better than just looking at a table

  Scenario: Generate explanation for a stats query
    Given the user asks "Cuales son los jugadores del Real Madrid?"
    And the database returns stats for "Markus Howard" with "25.0" points
    When the chat endpoint processes the request
    Then the response should contain a "message" field
    And the message should mention "Sergio Llull"
    And the response should contain structured data
