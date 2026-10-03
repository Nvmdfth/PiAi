# TASK-001: Ready-to-go pi4 setup (general chat + coder), tool calls working

## Goal
`docker compose --profile pi4 build && up` yields a working llama.cpp router with
two main models, each drafted by qwen2.5-0.5b:
- `qwen2.5-1.5b-q4_0` (general chat)
- `qwen2.5-coder-1.5b-q4_0` (coder)
Any fix must live in the repo (configs/, docker/, scripts/) so a rebuild reproduces it.

## Known defect
Coder returns its tool call as a fenced JSON block in `message.content` and no
`tool_calls` (template is identical to the general model; model ignores `<tool_call>`).
Server-side tool_choice / system prompt mitigations failed (see QA report in session).

## Acceptance (@qa-automation)
1. Both models pass tt.py: single_call, roundtrip, selection, no_tool.
2. Coder passes at temp 0 across N=3 runs.
3. Fix is reproduced from a clean container recreate (no manual steps).
4. `/v1/models` lists exactly the 3 pi4 models.
5. pi5 compose config still valid.
