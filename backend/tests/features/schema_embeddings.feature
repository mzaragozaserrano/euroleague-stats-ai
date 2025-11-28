Feature: Schema Embeddings Vectorization
  As a backend system
  I want to generate and store embeddings for schema metadata
  So that I can perform RAG-based schema retrieval for SQL generation

  Scenario: Generate embeddings for table descriptions
    Given I have metadata descriptions for schema tables
    When I generate embeddings using OpenAI
    Then the embeddings should have 1536 dimensions
    And the embeddings should be stored in schema_embeddings table

  Scenario: Retrieve relevant schema by similarity
    Given the schema_embeddings table contains multiple embeddings
    When I query for "puntos de jugadores"
    Then I should receive relevant schema descriptions
    And the results should be ordered by cosine similarity score

  Scenario: Clear and reinitialize embeddings
    Given the schema_embeddings table has existing data
    When I clear all schema embeddings
    Then the table should be empty
    When I reinitialize with metadata
    Then the embeddings should be successfully stored

  Scenario: Handle API errors gracefully
    Given OpenAI API is temporarily unavailable
    When I attempt to generate embeddings
    Then the system should raise an exception
    And log the error appropriately
    And not corrupt existing embeddings

  Scenario: Validate embedding dimensions
    Given I have successfully generated embeddings
    When I query the database for stored embeddings
    Then each embedding should have exactly 1536 dimensions
    And the embedding type should be vector

  Scenario: Retrieve top-k similar schemas
    Given the schema_embeddings table has at least 5 embeddings
    When I perform a similarity search with limit=3
    Then I should receive exactly 3 results
    And results should be sorted by similarity score descending

