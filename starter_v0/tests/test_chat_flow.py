"""Offline regression coverage of control flow; these are not live transcripts."""
from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall


class ScriptedProvider:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, *args, **kwargs):
        return next(self.responses)


def run(provider):
    return run_model_tool_loop(provider=provider, messages=[], tools=[], model=None, max_tool_rounds=3)


def test_save_note_pauses_with_actual_confirmation_question():
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall('save_note', {'filename': 'demo.md', 'content': '# Demo', 'confirmed': False})])])
    result = run(provider)
    assert result['status'] == 'waiting_for_user'
    assert 'demo.md' in result['assistant_text']
    assert result['tool_events'][0]['result']['response_type'] == 'yes_no'


def test_clarification_stops_before_any_later_side_effect():
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall('clarify', {'question': 'Which URL?'}), ToolCall('send', {'text': 'must not send', 'confirmed': True})])])
    result = run(provider)
    assert result['status'] == 'waiting_for_user'
    assert len(result['tool_events']) == 1


def test_no_tool_response_finishes_without_execution():
    result = run(ScriptedProvider([ModelResponse(text='Canceled.')]))
    assert result['status'] == 'answered'
    assert result['tool_events'] == []
