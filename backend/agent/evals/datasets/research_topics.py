from braintrust import EvalCase

# ─────────────────────────────────────────────────────────────────────────
# RESEARCH TOPIC DATASET — Research Sub-Agent Fidelity
#
# Inputs-only (no `expected`): the research sub-agent is graded reference-free
# against its own system prompt (SUBAGENT_SYSTEM_PROMPT) and the evidence its
# live searches actually returned. Each case is a single free-text research
# `topic` — exactly the shape the Supervisor dispatches (see test_subagent.py
# and build_user_message).
#
# Each topic is engineered to stress a specific fidelity dimension, mirroring
# the per-dimension coverage map in planner_edge_cases.py.
#
# Coverage map:
#   1. thin_results_honest_gaps            -> context_recall (honest GAPS) +
#                                             citation_integrity (no fabrication)
#   2. single_denomination_scope_discipline -> search_strategy_efficiency
#                                             (domain_scope not padded)
#   3. neutral_topic_scope_discipline      -> search_strategy_efficiency
#                                             (academic_neutral scope, non-
#                                             redundant follow-ups) +
#                                             context_recall (thematic merge)
#   4. fact_dense_citation_integrity       -> citation_integrity (dates,
#                                             councils, quoted wording and
#                                             scripture must all trace to a
#                                             returned highlight)
#
# Every topic is a SINGLE research assignment, which is all the Supervisor ever
# dispatches: it decomposes a question into one-topic-per-sub-agent, so a topic
# that asks one sub-agent to compare two traditions' positions, or to cover two
# unrelated subjects in one run, does not occur in production and is not tested
# here.
#
# Graded on EVERY case, so no case targets it specifically: report-format
# compliance (the skeleton in SUBAGENT_SYSTEM_PROMPT — sections present, empty
# ones dropped, no preamble) is scored under context_recall, and its violations
# are reported in recall_gaps / recall_superfluous under a `format:` prefix.
# ─────────────────────────────────────────────────────────────────────────

RESEARCH_TOPIC_DATASET = [
    {
        # Deliberately obscure and narrow: the allowlist is unlikely to return
        # rich, on-point coverage. The honest move is a thin report that states
        # what was found, cites it, and names the shortfall under GAPS. The
        # failure mode is "filling in the gaps" from training data -- asserting
        # patristic detail with no returned source behind it -- which the
        # sub-agent's Core Constraint forbids.
        "topic": (
            "Early Syriac Christian interpretation of the Parable of the Ten "
            "Virgins (Matthew 25:1-13) before the fifth century, especially in "
            "Ephrem the Syrian and the Syriac exegetical tradition"
        ),
        "metadata": {
            "case_id": "thin_results_honest_gaps",
            "category": "thin_results",
            "primary_dimension": "context_recall + citation_integrity",
            "tests": (
                "Allowlist coverage of pre-fifth-century Syriac exegesis is "
                "likely thin. The report must cite only what search returned "
                "and declare the shortfall in GAPS -- an honest 'not found' is "
                "correct and must be rewarded. It must NOT supply Ephrem "
                "quotes, dates, or attributed claims from training data with no "
                "returned source (citation_integrity: unsourced_fact / "
                "no fabrication)."
            ),
        },
    },
    {
        # A single named tradition. Policy: domain_scope should be ["catholic"]
        # (optionally academic_neutral for historical framing), NOT padded with
        # reformed/orthodox/etc., since every extra category dilutes results
        # with pages about someone else's position. main_query should be
        # keyword-dense (proper nouns, doctrine names); guiding_query a full
        # natural-language statement of what to extract.
        "topic": (
            "The Catholic Church's magisterial and scriptural basis for the "
            "dogma of the Immaculate Conception of Mary, including Ineffabilis "
            "Deus and the reasoning offered for it"
        ),
        "metadata": {
            "case_id": "single_denomination_scope_discipline",
            "category": "single_denomination",
            "primary_dimension": "search_strategy_efficiency",
            "tests": (
                "domain_scope should target ['catholic'] (academic_neutral "
                "acceptable for history); padding with other traditions the "
                "topic never invokes is padded_domain_scope. main_query must be "
                "keyword-dense and distinct from a full-sentence guiding_query. "
                "Findings should stay inside the Catholic frame."
            ),
        },
    },
    {
        # A textual/historical question that names no tradition at all, and has
        # several genuinely distinct facets (manuscript witnesses, patristic
        # citation, internal style/vocabulary evidence). Policy: domain_scope
        # should be ["academic_neutral"] (general_evangelical acceptable);
        # answering it out of one denomination's sources is a scope error and
        # padding it with denominations the topic never names is waste. The facets
        # are what make the budget interesting -- each follow-up must close one of
        # them rather than re-ask the first query in new words.
        "topic": (
            "The manuscript and patristic evidence bearing on whether the longer "
            "ending of Mark (Mark 16:9-20) belongs to the original text of the "
            "Gospel, and how it came to stand in the received text"
        ),
        "metadata": {
            "case_id": "neutral_topic_scope_discipline",
            "category": "no_tradition",
            "primary_dimension": "search_strategy_efficiency + context_recall",
            "tests": (
                "A topic invoking no tradition should get "
                "domain_scope ['academic_neutral'] (general_evangelical "
                "acceptable); answering it out of a single denomination's "
                "sources is wrong_domain_scope and naming traditions the topic "
                "never raises is padded_domain_scope. Because the topic has "
                "several nameable facets, each follow-up search must close a "
                "distinct one -- a re-phrased repeat is redundant_search. Recall "
                "must group findings by theme rather than by search, merging a "
                "point that surfaced in two searches into one line carrying both "
                "citation numbers."
            ),
        },
    },
    {
        # Saturated with exactly the specifics an LLM already carries: the date,
        # the four adverbs of the definition, Leo's Tome, the figures it was
        # written against. That prior knowledge is the trap -- every date, name,
        # quoted phrase and scripture reference must trace to a returned
        # highlight, and asserting one from memory is training-data leakage even
        # when it is perfectly accurate.
        "topic": (
            "The Definition of Chalcedon (451) on the two natures of Christ: its "
            "wording, the controversy it was written to settle, and the earlier "
            "documents and scriptural texts it drew on"
        ),
        "metadata": {
            "case_id": "fact_dense_citation_integrity",
            "category": "fact_dense_history",
            "primary_dimension": "citation_integrity",
            "tests": (
                "Every checkable specific -- the 451 date, council canons, named "
                "figures, the definition's quoted phrasing, and any scripture "
                "reference -- must be carried by a returned highlight and a "
                "resolvable citation number. Supplying one from training data is "
                "unsourced_fact even if correct; reconstructing the definition's "
                "wording more precisely than the highlight gave it is "
                "misrepresented_source; scripture must appear exactly as the "
                "source gave it, with no verse text supplied. What search did not "
                "return belongs in GAPS."
            ),
        },
    },
]


def build_research_topic_dataset():
    return [
        EvalCase(
            input={"topic": data["topic"]},
            expected=None,
            metadata=data.get("metadata"),
        )
        for data in RESEARCH_TOPIC_DATASET
    ]
