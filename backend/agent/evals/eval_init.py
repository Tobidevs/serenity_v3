from agent.evals.plan_decision_fidelity import planner_decision_fidelity
from braintrust import Eval
from agent.evals.datasets import build_planner_dataset
from agent.evals.tasks import planner_eval_task

Eval(
    "Serenity", 
    data=build_planner_dataset(),
    task=planner_eval_task,
    scores=[planner_decision_fidelity],
    experiment_name="planner_decision_fidelity",
)