from agent.evals.plan_decision_fidelity import planner_decision_fidelity
from braintrust import Eval
from agent.evals.datasets.planner_use_cases import build_planner_use_case_dataset
from agent.evals.datasets.planner_edge_cases import build_planner_edge_case_dataset
from agent.evals.datasets.research_topics import build_research_topic_dataset
from agent.evals.tasks import planner_eval_task, research_eval_task
from agent.evals.research_fidelity import research_fidelity
from app.tracing import setup_tracing

setup_tracing()

# Eval(
#     "Serenity", 
#     data=build_planner_edge_case_dataset(),
#     task=planner_eval_task,
#     scores=[planner_decision_fidelity],
#     experiment_name="planner_decision_fidelity",
# )

Eval(
    "Serenity",
    data=build_research_topic_dataset(),
    task=research_eval_task,
    scores=[research_fidelity],
    experiment_name="research_fidelity",
)