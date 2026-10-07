Feature: A movie night from discovery to ticket
  Moviegoers can choose available seats and manage only their own bookings.
  The website and API must always show the same reservation state.

  Background:
    Given a movie with an available seat A1

  Scenario: Browse the movie lineup without signing in
    When I request the movie API
    Then the movie is listed as JSON
    And the movie appears on the website

  Scenario: Book through the website and see the same ticket in the API
    Given I am signed in
    When I book seat A1 on the website
    Then my ticket appears on the history page
    And the API contains my reservation
    And seat A1 is unavailable

  Scenario: A second moviegoer cannot reserve an occupied seat
    Given I am signed in
    And another moviegoer has booked seat A1
    When I try to book seat A1 using the API
    Then the API rejects the duplicate booking
    And exactly one booking exists

  Scenario: Booking history belongs to its owner
    Given I am signed in
    And another moviegoer has booked seat A1
    When I request my booking history
    Then my API history is empty
    And I cannot retrieve or cancel the other ticket

  Scenario: Cancel a ticket and make its seat available again
    Given I am signed in
    When I book seat A1 on the website
    And I cancel my ticket using the API
    Then seat A1 is available
    And my website history is empty

  Scenario: Anonymous visitors cannot reserve seats
    When I try to book seat A1 using the API
    Then the API requires authentication
    And no booking exists
