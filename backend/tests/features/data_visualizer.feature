Feature: Data Visualizer Component

  Background:
    Given the DataVisualizer component is available
    And the Recharts library is installed

  Scenario: Render BarChart with valid data
    Given a list of valid numeric data with categories
    When the visualization type is "bar"
    Then a BarChart component should be rendered
    And the chart should display all data points correctly

  Scenario: Render LineChart with valid data
    Given a list of valid numeric data with categories
    When the visualization type is "line"
    Then a LineChart component should be rendered
    And the chart should display a continuous line

  Scenario: Render DataTable with valid data
    Given a list of valid data objects
    When the visualization type is "table"
    Then a table should be rendered
    And the table should display all columns and rows

  Scenario: Handle empty data gracefully
    Given an empty data array
    When the visualization type is "table"
    Then an error message should be displayed
    And "No hay datos para mostrar" message should be visible

  Scenario: Handle invalid data gracefully
    Given data that is not an array or is null
    When the component tries to render
    Then an error card should be displayed
    And "Datos inválidos" message should be visible

  Scenario: Auto-detect numeric columns for charts
    Given data with mixed string and numeric columns
    When the visualization type is "bar"
    Then only numeric columns should be used for the Y-axis
    And the first string column should be used for the X-axis

  Scenario: Mobile responsive visualization
    Given valid chart data
    When the viewport width is small (mobile)
    Then the chart should resize responsively
    And labels should be rotated if necessary
    And the table should have horizontal scroll on mobile

  Scenario: Render chart with title
    Given valid data and a title
    When the visualization type is "bar"
    Then the chart should display the title above it
    And the title should be visible and properly formatted

  Scenario: Handle special characters in data
    Given data with special characters (ñ, á, é, etc.)
    When rendering the visualization
    Then special characters should display correctly
    And no encoding errors should occur

  Scenario: Multiple numeric columns in bar chart
    Given data with multiple numeric columns
    When the visualization type is "bar"
    Then the first numeric column should be displayed
    And colors should be applied progressively

