# Agent Blast Radius

Ranks AI agents by the sensitive data they can reach and whether they can move it out.
Runs on synthetic data. Python standard library only.

## The problem
[2-3 sentences: agents inherit permissions and connectors; maker credentials and
connected sites can expose labeled data; prompt injection turns that into exfiltration.]

## How it works
score = (sum of label weight x sensitive items) x capability x identity x audience
Any agent with private data + untrusted content + an outbound path is Critical.
[Table of weights and one sentence of reasoning each.]

## Results
[Paste the leaderboard. One sentence on why the top agent is the top agent.]

## Design decision
[Your answer to the Session 2 design question: trifecta vs raw score.]

## Mapping to real controls
- Maker credentials -> Copilot Studio end-user authentication / maker credential controls
- High-labeled sources -> Purview DLP for Microsoft 365 Copilot, Restricted Content Discovery
- Oversharing -> Purview DSPM data risk assessments

## Limits
Heuristic, not a probability. Synthetic data. Weights are judgment calls.

## Run it
python blast_radius.py