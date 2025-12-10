Feature: Lazy Data Ingestion
  As a user
  I want to query historical data (e.g., 2024) not currently in the database
  So that the system automatically retrieves it from the external API and answers my question

  Scenario: User asks for stats from a missing season
    Given the database has no data for season "E2024"
    When the user sends the message "Dime los puntos de Larkin en 2024"
    Then the system should trigger the data ingestion for season "E2024"
    And the system should return a valid response with stats



