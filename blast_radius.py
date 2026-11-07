"""Agent Blast Radius: rank AI agents by the sensitive data they can reach
and whether they can move it out. Synthetic data only. Standard library only.
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Scoring weights. Change these and re-run to see how ranks shift.
LABEL_WEIGHTS = {"Public": 0, "Low": 1, "Medium": 3, "High": 5}

ACTION_WEIGHTS = {
    "read": 1,  # can see data
    "write": 2,  # can change data
    "share": 2,  # can widen access
    "send_email": 3,  # outbound path: data can leave
    "http_request": 3,  # outbound path: data can leave
}
OUTBOUND_ACTIONS = {"send_email", "http_request"}

AUTH_WEIGHTS = {"end_user": 1.0, "maker": 1.5}
AUDIENCE_WEIGHTS = {"team": 1.0, "org": 1.25}

PRIVATE_LABELS = {"Medium", "High"}

# Tier thresholds (score). Trifecta agents are always Critical.
TIERS = [(2000, "High"), (500, "Medium"), (0, "Low")]


def load_json(path):
    """Read a JSON file and return the Python object inside it."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def index_sources(sources):
    """Turn a list of sources into a dict keyed by id for fast lookup."""
    return {s["id"]: s for s in sources}


def source_exposure(source):
    """Sensitivity weight x number of sensitive items in one source."""
    return LABEL_WEIGHTS[source["label"]] * source["sensitive_items"]


def check_trifecta(agent_sources, actions):
    """Private data + untrusted content + outbound path, all at once."""
    has_private = any(s["label"] in PRIVATE_LABELS for s in agent_sources)
    has_untrusted = any(s["untrusted"] for s in agent_sources)
    has_outbound = any(a in OUTBOUND_ACTIONS for a in actions)
    return has_private and has_untrusted and has_outbound


def score_agent(agent, sources_by_id):
    """Return a dict with the agent's score, tier, riskiest path and flags."""
    agent_sources = [sources_by_id[sid] for sid in agent["sources"]]

    reach = sum(source_exposure(s) for s in agent_sources)
    capability = max(ACTION_WEIGHTS[a] for a in agent["actions"])
    identity = AUTH_WEIGHTS[agent["auth"]]
    audience = AUDIENCE_WEIGHTS[agent["shared_with"]]

    score = round(reach * capability * identity * audience)
    trifecta = check_trifecta(agent_sources, agent["actions"])

    if trifecta:
        tier = "Critical"
    else:
        tier = next(name for threshold, name in TIERS if score >= threshold)

    worst_source = max(agent_sources, key=source_exposure)
    worst_action = max(agent["actions"], key=lambda a: ACTION_WEIGHTS[a])
    path = f"{worst_source['name']} [{worst_source['label']}] -> {worst_action}"

    return {
        "agent": agent,
        "sources": agent_sources,
        "reach": reach,
        "capability": capability,
        "identity": identity,
        "audience": audience,
        "score": score,
        "tier": tier,
        "trifecta": trifecta,
        "path": path,
    }


def recommend(result):
    """Rule-based fixes. Each one maps to a real control to verify."""
    agent = result["agent"]
    recs = []
    if result["trifecta"]:
        recs.append("Break the trifecta: remove the outbound action or the "
                    "untrusted source (inbound mailbox or web).")
    if agent["auth"] == "maker":
        recs.append("Switch tool connections to end-user credentials so the "
                    "agent can only reach what each user can reach.")
        if agent["shared_with"] == "org":
            recs.append("Do not share org-wide while maker credentials are in "
                        "use; review safe-sharing enforcement.")
    if any(s["label"] == "High" for s in result["sources"]):
        recs.append("Review whether High Sensitivity sources belong in this "
                    "agent; consider DLP for Copilot (label-based) or "
                    "Restricted Content Discovery for those sites.")
    if any(s["external_sharing"] and s["label"] in PRIVATE_LABELS
           for s in result["sources"]):
        recs.append("A connected Medium/High source allows external sharing; "
                    "review sharing links on that site.")
    if not recs:
        recs.append("No priority fixes. Re-review when sources or actions change.")
    return recs


def build_report(results):
    lines = [
        "# Agent Blast Radius Report",
        "",
        f"Generated {date.today().isoformat()} from synthetic data.",
        "",
        "## Leaderboard",
        "",
        "| Rank | Agent | Tier | Score | Auth | Trifecta | Riskiest path |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for rank, r in enumerate(results, start=1):
        a = r["agent"]
        lines.append(
            f"| {rank} | {a['name']} | {r['tier']} | {r['score']:,} | "
            f"{a['auth']} | {'Yes' if r['trifecta'] else 'No'} | {r['path']} |"
        )

    lines += ["", "## Agent details", ""]
    for r in results:
        a = r["agent"]
        lines += [
            f"### {a['name']} ({r['tier']})",
            "",
            f"- Owner: {a['owner']}",
            f"- Score: {r['score']:,} = reach {r['reach']:,} x capability "
            f"{r['capability']} x identity {r['identity']} x audience {r['audience']}",
            f"- Sources: " + ", ".join(
                f"{s['name']} [{s['label']}]" for s in r["sources"]),
            f"- Actions: {', '.join(a['actions'])}",
            "- Recommended fixes:",
        ]
        lines += [f"    - {rec}" for rec in recommend(r)]
        lines.append("")

    lines += [
        "## Limits",
        "",
        "- Scores are a prioritization heuristic, not a probability of breach.",
        "- Weights are judgment calls; they are listed at the top of blast_radius.py.",
        "- Data is synthetic. Fixes are starting points to verify against current vendor docs.",
    ]
    return "\n".join(lines) + "\n"


def main():
    agents = load_json(ROOT / "data" / "agents.json")
    sources_by_id = index_sources(load_json(ROOT / "data" / "sources.json"))

    results = [score_agent(a, sources_by_id) for a in agents]
    tier_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    results.sort(key=lambda r: (tier_order[r["tier"]], -r["score"]))

    for r in results:
        print(f"{r['tier']:<9} {r['score']:>7,}  {r['agent']['name']}")

    report_path = ROOT / "report.md"
    report_path.write_text(build_report(results), encoding="utf-8")
    print(f"\nWrote {report_path.name}")


if __name__ == "__main__":
    main()
