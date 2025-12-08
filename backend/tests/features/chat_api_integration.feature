Feature: API Integration - Frontend to Backend Chat

  Background:
    Given the API server is available at "http://localhost:8000"
    And the frontend is running

  Scenario: Send a simple chat message successfully
    Given I have initialized the chat store
    When I send the message "¿Cuantos jugadores hay?"
    And the backend responds with SQL "SELECT COUNT(*) as total FROM players"
    And the response includes data with 1 record
    And the visualization type is "table"
    Then the message should be added to the history
    And the response should contain the SQL query
    And the response should contain the data

  Scenario: Handle backend errors gracefully
    Given I have initialized the chat store
    When I send the message "¿Jugadores con puntaje infinito?"
    And the backend responds with an error "I couldn't write the SQL query"
    Then the error message should be displayed
    And the error should not crash the frontend
    And the user should be able to send another message

  Scenario: Detect cold start (latency > 3s)
    Given I have initialized the chat store
    When I send the message "Test query"
    And the backend takes 3500 milliseconds to respond
    Then a cold start warning should be displayed
    And the message should contain "Despertando al agente..."

  Scenario: Detect rate limit (> 50 requests per day)
    Given I have initialized the chat store
    And I have sent 50 messages already
    When I try to send message number 51
    Then a rate limit warning should be displayed
    And the message should not be sent
    And the error should say "Rate limit alcanzado"

  Scenario: Handle network timeout (> 30s)
    Given I have initialized the chat store
    When I send the message "Test query"
    And the network times out after 30 seconds
    Then the error message should be displayed
    And the user should see "No se pudo conectar con el servidor"
    And the store should not be in loading state

  Scenario: Validate response format
    Given I have initialized the chat store
    When I send the message "Test query"
    And the backend responds with an invalid format
    Then the error should be caught and displayed
    And the error message should be "Respuesta invalida del servidor"

  Scenario: Persist chat history after API response
    Given I have initialized the chat store
    When I send the message "Message 1"
    And I receive a successful response
    And I send the message "Message 2"
    Then both messages should be in the history
    And the history should be persisted in localStorage
    And after page reload the history should still exist

  Scenario: Send message with conversation history
    Given I have initialized the chat store
    When I send the message "Message 1"
    And I receive a successful response
    And I send the message "Message 2 with context"
    Then the backend should receive both messages in the history
    And the second message should reference the first message

  Scenario: Handle visualization types correctly
    Given I have initialized the chat store
    When I send the message "¿Puntuacion por equipo?"
    And the backend responds with visualization type "bar"
    Then the response should include visualization "bar"
    And the DataVisualizer should be able to render it

  Scenario: Retry on network failure
    Given I have initialized the chat store
    When I send the message "Test query"
    And the first attempt times out
    And the second attempt succeeds
    Then the message should be displayed
    And no error should be shown

