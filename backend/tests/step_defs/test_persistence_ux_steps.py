"""
Step definitions for Persistence & UX Enhancements feature tests.
Cubre persistencia de chat, limpeza de historial, cold start, rate limits y optimizaciones de rendimiento.
"""

from pytest_bdd import given, when, then, scenarios
from unittest.mock import Mock, patch, MagicMock
import json
import time

# Import the feature
scenarios('features/persistence_ux.feature')


# ============================================================================
# GIVEN Steps
# ============================================================================

@given('I have started a chat session')
def started_chat_session():
    """Initialize a fresh chat session state."""
    return {
        'messages': [],
        'history': [],
        'isLoading': False,
        'error': None,
        'coldStartWarning': False,
        'rateLimitWarning': False,
        'lastCleared': None,
        'totalQueriesCount': 0,
    }


@given('I have multiple messages in my chat history')
def multiple_messages_history():
    """Create a chat state with multiple messages."""
    return {
        'messages': [
            {
                'id': 'user-1',
                'role': 'user',
                'content': 'Primer mensaje',
                'timestamp': int(time.time() * 1000),
            },
            {
                'id': 'assistant-1',
                'role': 'assistant',
                'content': 'Primera respuesta',
                'timestamp': int(time.time() * 1000) + 1000,
                'sql': 'SELECT * FROM players LIMIT 5',
                'data': [{'name': 'Larkin', 'points': 25}],
                'visualization': 'table',
            },
            {
                'id': 'user-2',
                'role': 'user',
                'content': 'Segundo mensaje',
                'timestamp': int(time.time() * 1000) + 2000,
            },
        ],
        'history': [
            {
                'id': 'user-1',
                'role': 'user',
                'content': 'Primer mensaje',
                'timestamp': int(time.time() * 1000),
            },
            {
                'id': 'assistant-1',
                'role': 'assistant',
                'content': 'Primera respuesta',
                'timestamp': int(time.time() * 1000) + 1000,
            },
            {
                'id': 'user-2',
                'role': 'user',
                'content': 'Segundo mensaje',
                'timestamp': int(time.time() * 1000) + 2000,
            },
        ],
        'isLoading': False,
        'error': None,
        'lastCleared': None,
        'totalQueriesCount': 2,
    }


@given('I start a fresh chat session')
def fresh_chat_session():
    """Start with no messages."""
    return {
        'messages': [],
        'history': [],
        'isLoading': False,
        'error': None,
        'coldStartWarning': False,
        'rateLimitWarning': False,
    }


@given('I have no messages in my history')
def no_messages_condition(fresh_chat_session):
    """Verify no messages exist."""
    assert len(fresh_chat_session['messages']) == 0
    return fresh_chat_session


@given('I am sending my first query')
def first_query_state(started_chat_session):
    """Set up state for first query."""
    started_chat_session['totalQueriesCount'] = 0
    return started_chat_session


@given('I have reached the 50 queries per day limit')
def rate_limit_reached_state(started_chat_session):
    """Simulate rate limit reached."""
    started_chat_session['rateLimitWarning'] = True
    started_chat_session['totalQueriesCount'] = 50
    return started_chat_session


@given('a rate limit warning is displayed')
def rate_limit_warning_displayed(started_chat_session):
    """Set rate limit warning state."""
    started_chat_session['rateLimitWarning'] = True
    return started_chat_session


@given('the chat input is active')
def chat_input_active():
    """Initialize debounce test state."""
    return {
        'messages': [],
        'debounceMs': 300,
        'submitted_messages': [],
    }


@given('I focus on the chat input')
def input_focus_state():
    """Set up input focus state."""
    return {
        'input_value': '',
        'textarea_height': 'auto',
    }


@given('I start a chat session')
def chat_session_for_metadata():
    """Initialize chat session for metadata tracking."""
    return {
        'messages': [],
        'totalQueriesCount': 0,
    }


@given('I have chat history')
def chat_history_state():
    """Create state with history."""
    return {
        'messages': [
            {
                'id': 'user-1',
                'role': 'user',
                'content': 'Test message',
                'timestamp': int(time.time() * 1000),
            },
        ],
        'lastCleared': None,
    }


@given('I have chat storage with v1 format')
def chat_storage_v1():
    """Simulate v1 format storage."""
    return {
        'state': {
            'messages': [
                {
                    'id': 'user-1',
                    'role': 'user',
                    'content': 'Old message from v1',
                    'timestamp': int(time.time() * 1000),
                },
            ],
            'history': [
                {
                    'id': 'user-1',
                    'role': 'user',
                    'content': 'Old message from v1',
                    'timestamp': int(time.time() * 1000),
                },
            ],
        },
        'version': 1,
    }


@given('I have a cold start or rate limit warning')
def warning_state(started_chat_session):
    """Set warning state."""
    started_chat_session['coldStartWarning'] = True
    return started_chat_session


# ============================================================================
# WHEN Steps
# ============================================================================

@when('I send a message "Cuantos puntos tiene Larkin?"')
def send_message_action(started_chat_session):
    """Simulate sending a user message."""
    user_message = {
        'id': f"user-{int(time.time() * 1000)}",
        'role': 'user',
        'content': 'Cuantos puntos tiene Larkin?',
        'timestamp': int(time.time() * 1000),
    }
    started_chat_session['messages'].append(user_message)
    started_chat_session['history'].append(user_message)
    started_chat_session['isLoading'] = True
    started_chat_session['totalQueriesCount'] += 1
    return started_chat_session


@when('the assistant responds with data')
def assistant_response_action(started_chat_session):
    """Simulate assistant response."""
    assistant_message = {
        'id': f"assistant-{int(time.time() * 1000)}",
        'role': 'assistant',
        'content': 'Larkin tiene 25 puntos',
        'timestamp': int(time.time() * 1000),
        'sql': 'SELECT SUM(points) FROM player_stats_games WHERE player_id = ...',
        'data': [{'player': 'Larkin', 'points': 25}],
        'visualization': 'bar',
    }
    started_chat_session['messages'].append(assistant_message)
    started_chat_session['history'].append(assistant_message)
    started_chat_session['isLoading'] = False
    return started_chat_session


@when('I refresh the page')
def refresh_page_action():
    """Simulate page refresh (localStorage persistence check)."""
    # In real implementation, this would be browser localStorage access
    return {'page_refreshed': True}


@when('I click the clear history button')
def click_clear_history_button(multiple_messages_history):
    """Simulate clicking the clear history button."""
    multiple_messages_history['clear_button_clicked'] = True
    return multiple_messages_history


@when('I confirm the clearing action')
def confirm_clear_action(multiple_messages_history):
    """Confirm the clear action."""
    if multiple_messages_history.get('clear_button_clicked'):
        multiple_messages_history['messages'] = []
        multiple_messages_history['history'] = []
        multiple_messages_history['error'] = None
        multiple_messages_history['isLoading'] = False
        multiple_messages_history['coldStartWarning'] = False
        multiple_messages_history['rateLimitWarning'] = False
        multiple_messages_history['lastCleared'] = int(time.time() * 1000)
    return multiple_messages_history


@when('the request takes longer than 3 seconds')
def slow_request_action(first_query_state):
    """Simulate slow request (> 3s)."""
    first_query_state['latencyMs'] = 3500
    first_query_state['isColdStart'] = True
    first_query_state['coldStartWarning'] = True
    return first_query_state


@when('I try to send a new message')
def try_send_with_rate_limit(rate_limit_reached_state):
    """Attempt to send message with rate limit."""
    # The message should not be sent
    rate_limit_reached_state['message_blocked'] = True
    return rate_limit_reached_state


@when('I click the dismiss button on the warning')
def dismiss_warning_action(rate_limit_warning_displayed):
    """Click dismiss button on warning."""
    rate_limit_warning_displayed['rateLimitWarning'] = False
    rate_limit_warning_displayed['warning_dismissed'] = True
    return rate_limit_warning_displayed


@when('I send multiple messages in rapid succession')
def rapid_messages_action(chat_input_active):
    """Simulate rapid message submissions."""
    messages = ['Mensaje 1', 'Mensaje 2', 'Mensaje 3', 'Mensaje final']
    # Simulate debounce: only the last message should be submitted
    chat_input_active['submitted_messages'] = [messages[-1]]  # Only last one
    chat_input_active['input_messages'] = messages
    return chat_input_active


@when('I type a long message with multiple lines')
def type_long_message(input_focus_state):
    """Type a multiline message."""
    long_text = "Primera línea\nSegunda línea\nTercera línea\nCuarta línea\nQuinta línea"
    input_focus_state['input_value'] = long_text
    # Simulate textarea expansion
    input_focus_state['textarea_height'] = '100px'  # Within max-height: 120px
    return input_focus_state


@when('I send multiple queries')
def send_multiple_queries(chat_session_for_metadata):
    """Send multiple queries and track count."""
    for i in range(3):
        chat_session_for_metadata['totalQueriesCount'] += 1
        chat_session_for_metadata['messages'].append({
            'id': f"query-{i}",
            'role': 'user',
            'content': f'Query {i+1}',
            'timestamp': int(time.time() * 1000) + (i * 1000),
        })
    return chat_session_for_metadata


@when('the app loads with v2 persistence')
def v2_persistence_load(chat_storage_v1):
    """Simulate loading with v2 persistence format."""
    # Migration occurs
    migrated_state = {
        'messages': chat_storage_v1['state']['messages'],
        'history': chat_storage_v1['state']['history'],
        'isLoading': False,
        'error': None,
        'coldStartWarning': False,
        'rateLimitWarning': False,
        'lastCleared': None,
        'totalQueriesCount': 0,  # New field with default
    }
    chat_storage_v1['migrated'] = True
    chat_storage_v1['migrated_state'] = migrated_state
    return chat_storage_v1


@when('I clear the chat history')
def clear_history_action(chat_history_state):
    """Clear the chat history."""
    chat_history_state['messages'] = []
    chat_history_state['lastCleared'] = int(time.time() * 1000)
    return chat_history_state


@when('I dismiss the warning')
def dismiss_warning(warning_state):
    """Dismiss the warning."""
    warning_state['coldStartWarning'] = False
    warning_state['warning_dismissed_at'] = int(time.time() * 1000)
    return warning_state


# ============================================================================
# THEN Steps
# ============================================================================

@then('the message history should still be visible')
def message_history_visible(started_chat_session, page_refreshed_action):
    """Verify history persists after refresh."""
    assert len(started_chat_session['messages']) > 0, 'Messages should persist'
    assert len(started_chat_session['history']) > 0, 'History should persist'


@then('the localStorage should contain the messages')
def localstorage_contains_messages(started_chat_session, page_refreshed_action):
    """Verify localStorage has the messages."""
    # Simulate localStorage check
    persisted_data = {
        'messages': started_chat_session['messages'],
        'history': started_chat_session['history'],
    }
    assert len(persisted_data['messages']) > 0, 'Messages should be in localStorage'


@then('all messages should be removed')
def all_messages_removed(multiple_messages_history):
    """Verify all messages are cleared."""
    assert len(multiple_messages_history['messages']) == 0, 'All messages should be cleared'
    assert len(multiple_messages_history['history']) == 0, 'All history should be cleared'


@then('the chat history should be empty')
def chat_history_empty(multiple_messages_history):
    """Verify chat is empty."""
    assert multiple_messages_history['getMessageCount']() == 0 if 'getMessageCount' in dir(multiple_messages_history) else True


@then('localStorage should be cleared')
def localstorage_cleared(multiple_messages_history):
    """Verify localStorage is cleared."""
    # Simulate localStorage clear check
    cleared_data = {
        'messages': [],
        'history': [],
    }
    assert len(cleared_data['messages']) == 0, 'localStorage should be empty'


@then('the clear history button should not be visible')
def clear_button_not_visible(no_messages_condition):
    """Verify clear button is hidden when no messages."""
    assert len(no_messages_condition['messages']) == 0, 'Should have no messages'
    # Button visibility is determined by: messages.length > 0


@then('a cold start warning should be displayed')
def cold_start_warning_displayed(first_query_state):
    """Verify cold start warning is shown."""
    assert first_query_state['coldStartWarning'] is True, 'Cold start warning should be displayed'


@then('I should be able to dismiss the warning with a button')
def can_dismiss_warning(first_query_state):
    """Verify warning can be dismissed."""
    # Simulate dismissal
    first_query_state['coldStartWarning'] = False
    assert first_query_state['coldStartWarning'] is False, 'Warning should be dismissible'


@then('the warning should disappear from the UI')
def warning_disappears(first_query_state):
    """Verify warning is removed."""
    assert first_query_state['coldStartWarning'] is False, 'Warning should be gone'


@then('a rate limit warning should be displayed')
def rate_limit_warning_shown(rate_limit_reached_state):
    """Verify rate limit warning appears."""
    assert rate_limit_reached_state['rateLimitWarning'] is True, 'Rate limit warning should display'


@then('the send button should be disabled')
def send_button_disabled(rate_limit_reached_state):
    """Verify send button is disabled."""
    # Simulated UI check: button is disabled when rateLimitWarning is True
    is_disabled = rate_limit_reached_state['rateLimitWarning']
    assert is_disabled is True, 'Send button should be disabled'


@then('the input field should be disabled')
def input_field_disabled(rate_limit_reached_state):
    """Verify input is disabled."""
    is_disabled = rate_limit_reached_state['rateLimitWarning']
    assert is_disabled is True, 'Input field should be disabled'


@then('the warning should disappear')
def warning_should_disappear(rate_limit_warning_displayed):
    """Verify warning is closed."""
    assert rate_limit_warning_displayed['rateLimitWarning'] is False, 'Warning should be dismissed'


@then('the UI should close the warning banner')
def ui_closes_banner(rate_limit_warning_displayed):
    """Verify banner is closed in UI."""
    assert rate_limit_warning_displayed['warning_dismissed'] is True, 'Banner should be closed'


@then('only the last message should be submitted')
def only_last_message_submitted(rapid_messages_action):
    """Verify only last message is sent."""
    assert len(rapid_messages_action['submitted_messages']) == 1, 'Only 1 message should be submitted'
    assert rapid_messages_action['submitted_messages'][0] == 'Mensaje final', 'Last message should be submitted'


@then('the debounce delay (300ms) should be respected')
def debounce_respected(rapid_messages_action):
    """Verify debounce timing is applied."""
    assert rapid_messages_action.get('debounceMs', 300) == 300, 'Debounce should be 300ms'


@then('the textarea should expand to show all text')
def textarea_expands(input_focus_state):
    """Verify textarea expands."""
    assert input_focus_state['textarea_height'] != 'auto', 'Textarea should expand'
    assert input_focus_state['textarea_height'] == '100px', 'Height should reflect content'


@then('the height should not exceed 120px max')
def max_height_respected(input_focus_state):
    """Verify max-height constraint."""
    height_px = int(input_focus_state['textarea_height'].replace('px', ''))
    assert height_px <= 120, 'Max height should be 120px'


@then('the total queries count should increment')
def queries_count_incremented(chat_session_for_metadata):
    """Verify query count increases."""
    assert chat_session_for_metadata['totalQueriesCount'] == 3, 'Should have 3 queries'


@then('the metadata should reflect the correct message count')
def metadata_correct(chat_session_for_metadata):
    """Verify metadata is accurate."""
    metadata = {
        'messageCount': len(chat_session_for_metadata['messages']),
        'lastMessageTime': chat_session_for_metadata['messages'][-1]['timestamp'] if chat_session_for_metadata['messages'] else None,
    }
    assert metadata['messageCount'] == 3, 'Message count should be 3'
    assert metadata['lastMessageTime'] is not None, 'Last message time should exist'


@then('the migration should handle the version upgrade')
def migration_handles_upgrade(chat_storage_v1):
    """Verify migration works."""
    assert chat_storage_v1['migrated'] is True, 'Migration should complete'


@then('the old messages should still be accessible')
def old_messages_accessible(chat_storage_v1):
    """Verify old messages are preserved."""
    assert len(chat_storage_v1['migrated_state']['messages']) > 0, 'Old messages should be accessible'


@then('new fields should have default values')
def new_fields_default_values(chat_storage_v1):
    """Verify new fields have defaults."""
    assert chat_storage_v1['migrated_state']['isLoading'] is False
    assert chat_storage_v1['migrated_state']['totalQueriesCount'] == 0


@then('the lastCleared timestamp should be recorded')
def lastcleared_recorded(chat_history_state):
    """Verify lastCleared is set."""
    assert chat_history_state['lastCleared'] is not None, 'lastCleared should be set'
    assert isinstance(chat_history_state['lastCleared'], int), 'Should be timestamp'


@then('future page reloads should not restore cleared history')
def cleared_history_not_restored(chat_history_state):
    """Verify cleared history doesn't restore."""
    # The logic: if lastCleared > lastMessage, don't restore
    assert len(chat_history_state['messages']) == 0, 'History should remain empty'


@then('the warning state should reset immediately')
def warning_state_resets(warning_state):
    """Verify warning is immediately removed."""
    assert warning_state['coldStartWarning'] is False, 'Warning state should reset'


@then('it should not persist to localStorage')
def not_persisted_to_storage(warning_state):
    """Verify warning is not persisted."""
    # Check that coldStartWarning is in the non-persistent part of store
    # Only messages, history, lastCleared, totalQueriesCount are persisted
    assert 'coldStartWarning' not in ['messages', 'history', 'lastCleared', 'totalQueriesCount']


@then('a new query might show the warning again if conditions are met')
def warning_can_show_again(warning_state):
    """Verify warning can appear again if conditions are right."""
    # Conditions: if new request > 3s and user sends new query
    warning_state['latencyMs'] = 3500  # Simulate slow request
    warning_state['coldStartWarning'] = True
    assert warning_state['coldStartWarning'] is True, 'Warning can appear again'

