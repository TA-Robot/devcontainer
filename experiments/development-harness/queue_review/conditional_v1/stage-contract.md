# Stage-specific extension (takes precedence over the earlier deliverable list)

All stages have the same queue behavioral requirements and public tools.
The drafter first investigates and may repair the implementation and add tests/test_repair.py.
It then writes review-request.json with exactly:

```json
{"action":"submit","reason":"What the investigation established","question":"","evidence":["queue_store.py"]}
```

Choose `submit` to finish with the current implementation, or `consult` to request one independent
review of the current implementation. Consult requires a nonempty specific question; submit requires
an empty question. Both require a nonempty reason and a nonempty list of distinct relative file paths
for evidence. Paths must identify regular files in this workspace, excluding review-request.json.
The request is at most 8192 bytes. It is routing data, not a quality score or permission to execute commands.
Both actions are allowed in both conditions; a consultation is not mandatory.

On consult, the controller stops and archives the drafter, gives its current implementation and question
to a fresh reviewer, then passes that same implementation and the review to a fresh final maker.
The reviewer may write only advice.json. The final maker may edit the three implementation files and
tests/test_repair.py only. There is at most one review; no stage may directly call agents or create other artifacts.
On submit, there is no reviewer or final-maker provider call. No change is a valid final result if requirements hold.
The shared condition budget includes initial investigation, the decision, optional review, handoff and final repair.
External evaluation runs only after all participant writers stop; its score is never used for routing.
