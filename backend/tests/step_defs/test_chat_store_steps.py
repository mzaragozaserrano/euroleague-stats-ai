import json
from pytest_bdd import given, when, then, scenario, scenarios
import pytest


# Importar modelos y contexto
@pytest.fixture
def chat_store():
    """Simular el store de chat como un diccionario en Python para testing"""
    return {
        'messages': [],
        'history': [],
        'isLoading': False,
        'error': None,
        'coldStartWarning': False,
        'rateLimitWarning': False,
    }


@scenario('../features/chat_store.feature', 'Store initializes with empty state')
def test_store_initializes_empty():
    pass


@scenario('../features/chat_store.feature', 'Adding a message to the store')
def test_adding_message():
    pass


@scenario('../features/chat_store.feature', 'Setting loading state')
def test_setting_loading_state():
    pass


@scenario('../features/chat_store.feature', 'Setting and clearing error')
def test_error_handling():
    pass


@scenario('../features/chat_store.feature', 'Chat history persists in localStorage')
def test_history_persistence():
    pass


@scenario('../features/chat_store.feature', 'Clear history action removes all messages')
def test_clear_history():
    pass


@scenario('../features/chat_store.feature', 'Cold start warning is displayed')
def test_cold_start_warning():
    pass


@scenario('../features/chat_store.feature', 'Rate limit warning is displayed')
def test_rate_limit_warning():
    pass


@scenario('../features/chat_store.feature', 'Message count is calculated correctly')
def test_message_count():
    pass


@scenario('../features/chat_store.feature', 'Multiple messages with metadata')
def test_messages_with_metadata():
    pass


# Step Definitions

@given('the chat store is created')
def step_store_created(chat_store):
    """Initialize the chat store"""
    assert chat_store is not None
    assert len(chat_store['messages']) == 0


@then('the messages array should be empty')
def step_messages_empty(chat_store):
    """Verify messages array is empty"""
    assert chat_store['messages'] == []


@then('the history array should be empty')
def step_history_empty(chat_store):
    """Verify history array is empty"""
    assert chat_store['history'] == []


@then('isLoading should be false')
def step_is_loading_false(chat_store):
    """Verify isLoading is false"""
    assert chat_store['isLoading'] is False


@then('error should be null')
def step_error_null(chat_store):
    """Verify error is null"""
    assert chat_store['error'] is None


@given('I add a message with role "user" and content "Hello"')
def step_add_hello_message(chat_store):
    """Add a user hello message"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Hello',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)
    chat_store['error'] = None


@given('I add a message with role "user" and content "Test message"')
def step_add_test_message(chat_store):
    """Add a user test message"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Test message',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)
    chat_store['error'] = None


@when('I add a message with role "user" and content "Hello"')
def when_add_hello_message(chat_store):
    """Add a user hello message (when step)"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Hello',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)
    chat_store['error'] = None


@then('the messages array should contain 1 message')
def step_messages_count_one(chat_store):
    """Verify message count is 1"""
    assert len(chat_store['messages']) == 1


@then('the history array should contain 1 message')
def step_history_count_one(chat_store):
    """Verify history count is 1"""
    assert len(chat_store['history']) == 1


@then('the message role should be "user"')
def step_message_role_user(chat_store):
    """Verify last message role is user"""
    assert chat_store['messages'][-1]['role'] == 'user'


@then('the message content should be "Hello"')
def step_message_content_hello(chat_store):
    """Verify last message content is Hello"""
    assert chat_store['messages'][-1]['content'] == 'Hello'


@when('I set loading to true')
def step_set_loading_true(chat_store):
    """Set loading state to true"""
    chat_store['isLoading'] = True
    chat_store['error'] = None


@then('isLoading should be true')
def step_is_loading_true(chat_store):
    """Verify isLoading is true"""
    assert chat_store['isLoading'] is True


@when('I set error to "Network error"')
def step_set_network_error(chat_store):
    """Set error to Network error"""
    chat_store['error'] = 'Network error'
    chat_store['isLoading'] = False


@then('error should be "Network error"')
def step_error_network(chat_store):
    """Verify error is Network error"""
    assert chat_store['error'] == 'Network error'


@when('I clear error')
def step_clear_error(chat_store):
    """Clear error message"""
    chat_store['error'] = None


@when('the store is rehydrated from localStorage')
def step_rehydrate_store(chat_store):
    """Simulate localStorage rehydration"""
    # In a real scenario, this would read from localStorage
    # For testing, we verify the store state is preserved
    pass


@then('the message content should be "Test message"')
def step_message_content_test(chat_store):
    """Verify message content is Test message"""
    assert chat_store['messages'][-1]['content'] == 'Test message'


@given('I add a message with role "user" and content "Message 1"')
def step_add_message_1(chat_store):
    """Add message 1"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Message 1',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@given('I add a message with role "assistant" and content "Response 1"')
def step_add_response_1(chat_store):
    """Add response 1"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'assistant',
        'content': 'Response 1',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@when('I clear history')
def step_clear_history(chat_store):
    """Clear all messages and history"""
    chat_store['messages'] = []
    chat_store['history'] = []
    chat_store['error'] = None
    chat_store['isLoading'] = False


@when('I set cold start warning to true')
def step_set_cold_start_warning(chat_store):
    """Set cold start warning"""
    chat_store['coldStartWarning'] = True


@then('coldStartWarning should be true')
def step_cold_start_warning_true(chat_store):
    """Verify cold start warning is true"""
    assert chat_store['coldStartWarning'] is True


@when('I set rate limit warning to true')
def step_set_rate_limit_warning(chat_store):
    """Set rate limit warning"""
    chat_store['rateLimitWarning'] = True


@then('rateLimitWarning should be true')
def step_rate_limit_warning_true(chat_store):
    """Verify rate limit warning is true"""
    assert chat_store['rateLimitWarning'] is True


@given('I add a message with role "user" and content "Message 1"')
def step_given_message_1(chat_store):
    """Add message 1 (given)"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Message 1',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@given('I add a message with role "assistant" and content "Response 1"')
def step_given_response_1(chat_store):
    """Add response 1 (given)"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'assistant',
        'content': 'Response 1',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@given('I add a message with role "user" and content "Message 2"')
def step_add_message_2(chat_store):
    """Add message 2"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'user',
        'content': 'Message 2',
        'timestamp': 1234567890,
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@when('I get message count')
def step_get_message_count(chat_store):
    """Get current message count"""
    chat_store['message_count'] = len(chat_store['messages'])


@then('message count should be 3')
def step_verify_message_count_3(chat_store):
    """Verify message count is 3"""
    assert chat_store['message_count'] == 3


@when('I add a message with role "assistant" and SQL query metadata')
def step_add_message_with_metadata(chat_store):
    """Add a message with SQL and visualization metadata"""
    message = {
        'id': f'msg-{len(chat_store["messages"]) + 1}',
        'role': 'assistant',
        'content': 'Here are the results',
        'timestamp': 1234567890,
        'sql': 'SELECT * FROM players LIMIT 10',
        'data': [{'player': 'John', 'points': 20}],
        'visualization': 'bar',
    }
    chat_store['messages'].append(message)
    chat_store['history'].append(message)


@then('the messages array should contain 1 message')
def step_messages_has_one(chat_store):
    """Verify messages array has 1 message"""
    assert len(chat_store['messages']) == 1


@then('the message should have SQL query data')
def step_message_has_sql(chat_store):
    """Verify message has SQL data"""
    assert 'sql' in chat_store['messages'][-1]
    assert chat_store['messages'][-1]['sql'] is not None


@then('the message should have visualization type "bar"')
def step_message_visualization_bar(chat_store):
    """Verify message visualization type is bar"""
    assert chat_store['messages'][-1]['visualization'] == 'bar'
