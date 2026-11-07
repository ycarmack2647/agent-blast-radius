# Agent Blast Radius

Ranks AI agents by the sensitive data they can reach and whether they can move it out.
Runs on synthetic data. Python standard library only.

## The problem
 Agents inherit permissions and connectors; maker credentials and
connected sites can expose labeled data; prompt injection turns that into exfiltration.]

## How it works
score = (sum of label weight x sensitive items) x capability x identity x audience
Any agent with private data + untrusted content + an outbound path is Critical.
[Table of weights and one sentence of reasoning each.]

## Results

| Rank | Agent | Tier | Score | Auth | Trifecta | Riskiest path |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Fare Dispute Triage | Critical | 4,050 | end_user | Yes | Fare Card Disputes site [Medium] -> send_email |
| 2 | Vendor Contract Summarizer | Critical | 1,215 | maker | Yes | Vendor Contracts site [Medium] -> http_request |
| 3 | HR Benefits Helper | High | 19,125 | maker | No | HR Employee Records site [High] -> send_email |
| 4 | IT Ticket Assistant | Low | 100 | end_user | No | IT Ticket table (Dataverse) [Low] -> write |
| 5 | Policy Q&A Bot | Low | 19 | end_user | No | Operations Procedures site [Low] -> read |

**Why Fare Dispute Triage is #1:** it reads Medium-sensitivity fare dispute data,
takes input from a customer mailbox that anyone outside the organization can email,
and can send email out, so a single malicious message could instruct it to leak that
data, and it has the higher score of the two agents meeting all three conditions.

HR Benefits Helper has the highest raw score (19,125) but ranks third: it can reach
more sensitive data, but it has no untrusted input, so an outsider has no direct way
to hijack it. Critical tier reflects how easy an attack is; score reflects how much
damage is possible.
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
