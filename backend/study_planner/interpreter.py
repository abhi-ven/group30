import json

from .config import get_model
from .pdf_reader import parse_json
from .prompts import DISRUPTION_PROMPT


def make_context(previous):
    """Give the model the real IDs so it can't invent them."""
    plan, state = previous["plan"], previous["state"]
    return {
        "now": state["now"],
        "tasks": [{"id": t["id"], "title": t["title"]} for t in state["tasks"]],
        "studyBlocks": [{"id": b["id"], "start": b["start"], "taskId": b["refId"]}
                        for b in plan["blocks"] if b["type"] == "task"],
        "events": [{"id": e["id"], "title": e["title"]} for e in state["fixedEvents"]],
    }


def interpret(raw, context):
    """Use with replan(..., interpreter=interpret, context=make_context(plan))."""
    reply = get_model().invoke([
        ("system", DISRUPTION_PROMPT),
        ("human", "Context:\n" + json.dumps(context) + "\n\nMessage: " + raw)])
    data = parse_json(reply.content)
    data["raw"] = raw
    return data  # replan validates this, retries once, then uses the rule-based fallback
