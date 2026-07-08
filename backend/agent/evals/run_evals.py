from braintrust import Eval
from .eval_datasets import build_planner_dataset

Eval(
    "Serenity", 
    data=build_planner_dataset()
)