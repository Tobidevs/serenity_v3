"""The distillation loop end to end, with a scripted model and a fake Exa.

The unit tests pin each piece; this pins the thing they cannot see between
them — that by the time the model writes its full report, the excerpts from
the first search are gone from what it is shown, while the numbers it needs to
cite them still resolve. Nothing here touches a network.
"""

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agent import subagent as sub
from agent import tools
from helpers import call, report


class FakeExa:
    """Stands in for the Exa client, returning a fresh page per search."""

    def __init__(self):
        self.calls = 0

    def search(self, **kwargs):
        self.calls += 1
        n = self.calls

        class Result:
            title = f"Page {n}"
            url = f"https://source{n}.org/article"
            favicon = f"https://source{n}.org/favicon.ico"
            highlights = [f"excerpt-{n}-alpha", f"excerpt-{n}-beta"]

        return type("Response", (), {"results": [Result()]})()


class ScriptedModel:
    """Replays a fixed list of turns, recording what it was shown each time."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.seen = []

    def invoke(self, messages):
        self.seen.append(list(messages))
        return self.responses.pop(0)


@pytest.fixture
def run_loop(monkeypatch):
    def run(responses):
        model = ScriptedModel(responses)
        monkeypatch.setattr(tools, "exa", FakeExa())
        monkeypatch.setattr(sub, "_subagent_model", lambda: model)

        result = sub.search_subagent.invoke(
            {
                "messages": [
                    SystemMessage(content="system"),
                    HumanMessage(content=sub.build_user_message("justification")),
                ],
                "sources": [],
                "steps": 0,
                "findings": [],
                "final_sources": [],
                "partial_reports": [],
                "search_trace": [],
            }
        )
        return result, model

    return run


def _search(call_id):
    return call(
        call_id,
        args={"main_query": "q", "guiding_query": "g", "domain_scope": ["catholic"]},
    )


def _text(messages):
    return "\n".join(
        str(m.content) for m in messages if isinstance(m, (ToolMessage, AIMessage))
    )


SCRIPT = [
    AIMessage(content="", tool_calls=[_search("s1")]),
    AIMessage(
        content="",
        tool_calls=[
            report("partial", findings="Page 1 says X [1]", call_id="r1"),
            _search("s2"),
        ],
    ),
    AIMessage(
        content="",
        tool_calls=[
            report("full", findings="X [1] and Y [2]", call_id="r2"),
        ],
    ),
]


def test_reported_excerpts_are_gone_by_the_final_turn(run_loop):
    _, model = run_loop(SCRIPT)

    final_turn = _text(model.seen[-1])

    # Search 1 was reported on, so its excerpts are gone...
    assert "excerpt-1-alpha" not in final_turn
    # ...but the model can still see that it saw that page, and its number.
    assert "[1] Page 1" in final_turn
    assert sub.STUB_MARKER in final_turn
    # Search 2 has not been reported on yet, so it is still there in full.
    assert "excerpt-2-alpha" in final_turn


def test_excerpts_are_present_on_the_turn_that_reports_them(run_loop):
    # The other half of the invariant: nothing is dropped before the model has
    # had a chance to distil it.
    _, model = run_loop(SCRIPT)

    assert "excerpt-1-alpha" in _text(model.seen[1])


def test_citation_numbers_stay_stable_across_searches(run_loop):
    # Page 2 must be [2], not another [1]. A partial report written on turn 2
    # cites numbers that have to still mean the same thing at the end.
    _, model = run_loop(SCRIPT)

    final_turn = _text(model.seen[-1])

    assert "[2] TITLE: Page 2" in final_turn
    assert "[1] Page 1" in final_turn


def test_final_report_carries_urls_the_model_never_saw(run_loop):
    result, model = run_loop(SCRIPT)

    findings = result["findings"][0]

    assert "SOURCES" in findings
    assert "[1] https://source1.org/article — Page 1" in findings
    assert "[2] https://source2.org/article — Page 2" in findings
    # The model was shown hosts, never full urls, on any turn.
    for turn in model.seen:
        assert "source1.org/article" not in _text(turn)


def test_partials_are_banked_as_the_run_goes(run_loop):
    result, _ = run_loop(SCRIPT)

    assert result["partial_reports"] == ["Page 1 says X [1]", "X [1] and Y [2]"]


def test_a_run_cut_short_still_returns_its_partials(run_loop):
    # The failure the old loop had: hitting a stop condition with no full
    # report meant the caller got nothing at all.
    cut_short = [
        AIMessage(content="", tool_calls=[_search("s1")]),
        AIMessage(
            content="",
            tool_calls=[report("partial", findings="Page 1 says X [1]", call_id="r1")],
        ),
    ]

    result, _ = run_loop(cut_short)

    assert result["findings"] == ["Page 1 says X [1]\n\nSOURCES\n[1] https://source1.org/article — Page 1"]


def test_two_reports_in_one_turn_are_both_banked(run_loop):
    # Routing acts on the full one, but the partial still has to survive:
    # banking only the call routing looked at would lose the other outright.
    script = [
        AIMessage(content="", tool_calls=[_search("s1")]),
        AIMessage(
            content="",
            tool_calls=[
                report("partial", findings="notes [1]", call_id="r1"),
                report("full", findings="final [1]", call_id="r2"),
            ],
        ),
    ]

    result, _ = run_loop(script)

    assert result["partial_reports"] == ["notes [1]", "final [1]"]
    assert result["findings"][0].startswith("final [1]")


def test_favicons_never_reach_the_model(run_loop):
    _, model = run_loop(SCRIPT)

    for turn in model.seen:
        assert "favicon" not in _text(turn)


def test_search_trace_keeps_what_the_model_was_shown(run_loop):
    # Snapshotted before stubbing, so the evidence behind an early report
    # survives even though the messages no longer carry it.
    result, _ = run_loop(SCRIPT)

    trace = "\n".join(result["search_trace"])

    assert "excerpt-1-alpha" in trace
    assert "excerpt-2-alpha" in trace


def test_only_search_results_are_ever_rewritten(run_loop):
    # Prefix caching matches the longest common prefix, and stubbing moves the
    # divergence point back to whichever message was rewritten. Confining
    # rewrites to exa_search results is what keeps that cost predictable: no
    # system, human or assistant message may ever change under the model.
    _, model = run_loop(SCRIPT)

    for earlier, later in zip(model.seen, model.seen[1:]):
        assert len(later) > len(earlier), "history must only grow"
        for i, before in enumerate(earlier):
            after = later[i]
            assert type(before) is type(after)
            if isinstance(before, ToolMessage) and before.name == "exa_search":
                continue
            assert str(before.content) == str(after.content)


def test_a_stub_is_never_rewritten_again(run_loop):
    # The guard STUB_MARKER exists for. Re-stubbing would drag the divergence
    # point back to an early message on every later turn, and the run would
    # stop reading cache almost entirely.
    longer = [
        AIMessage(content="", tool_calls=[_search("s1")]),
        AIMessage(
            content="",
            tool_calls=[report("partial", findings="one [1]", call_id="r1"), _search("s2")],
        ),
        AIMessage(
            content="",
            tool_calls=[report("partial", findings="two [2]", call_id="r2"), _search("s3")],
        ),
        AIMessage(content="", tool_calls=[report("full", findings="all [1][2][3]", call_id="r3")]),
    ]

    _, model = run_loop(longer)

    # Search 1's results are stubbed from the third turn on; the text must be
    # byte-identical every turn after that.
    # Index 3 is search 1's results; the opening turn is shorter than that.
    stubbed = [
        str(turn[3].content)
        for turn in model.seen
        if len(turn) > 3 and str(turn[3].content).startswith(sub.STUB_MARKER)
    ]

    assert len(stubbed) >= 2, "expected search 1 to stay stubbed across turns"
    assert len(set(stubbed)) == 1
