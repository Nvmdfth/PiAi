# Optimization Log (pi4 engine)

Living tracker of performance ideas: what was tried, what was measured, what is still open.
Update the status and evidence in the same change that tests an idea.

Hardware: Raspberry Pi 4 (4x Cortex-A72, 7.8 GB). Engine: `piai-engine`, llama-server in router
mode, `qwen2.5-1.5b-q4_0` + `qwen2.5-coder-1.5b-q4_0`, optional `qwen2.5-0.5b-q4_0` draft.

Status: `DONE` measured and decided · `RUNNING` in progress · `OPEN` not yet tested · `INVALID` earlier result discarded.

## Baseline (2026-10-02)

| What | Value | Source |
|---|---|---|
| Generation, 1.5B, draft off | 3.24-3.28 tok/s | side-server sweeps |
| Prompt processing, 1.5B | ~5-7 tok/s | live engine, `eval_prompt_cache.py` |
| Cold prefix, ~437 tokens | 76 s (general), 101 s (coder) | `eval_prompt_cache.py` |

## Tried

| Idea | Status | Result | Decision |
|---|---|---|---|
| Threads 3 vs 4 | DONE | 2.62 vs 2.64 tok/s (1.5B); 8.03 vs 7.58 (0.5B). Report section 2. | No gain. Keep 3. |
| Server prompt (prefix) cache | DONE | Warm request 5.7x (general) / 6.6x (coder) faster wall time; prompt-only ~19x; 420 of 437 tokens cached. | Already works with `cache_prompt`. The cost is the cold prefix. |
| Speculative decoding, n-max sweep (general, temp 0) | CONFOUNDED | tok/s: off 3.28, n2 2.84, n4 2.71, n6 2.58, n8 2.61. | Run order was off first, then n2..n8; speeds fall monotonically, as heating would. Needs interleaved re-test. |
| Draft acceptance rate (`llama-speculative`, n-max 4, one prompt) | DONE | 85% accepted (51/60) yet 2.75 tok/s. | Acceptance is not the problem. Hypothesis: batched verify has almost no discount on this CPU (prompt ~5 tok/s vs gen ~3.3), so draft steps are pure overhead. Untested. |
| Speculative decoding at production sampling, general | CONFOUNDED | off 3.24 vs n8 2.78 tok/s (-14%), seed 1. | Draft ran after the no-draft run; thermal confound not excluded. |
| Speculative decoding at production sampling, coder | CONFOUNDED | off 2.60 vs n8 2.64 tok/s (+1.5%, within noise), seed 1. | Neutral at best, measured while hot. |

## Open

Ordered by expected value; cold prefill (~5-7 tok/s) is the dominant latency.

| Idea | Why | Test |
|---|---|---|
| Remove draft from `configs/models_preset_pi4.ini` | APPLIED and committed; draft stays off by owner decision. Evidence is confounded (see below); RAM saving not observed (used 3110 -> 3101 MB, draft file is page-cache shared). | Interleaved on/off re-test with cooldown was started and abandoned (no data). Revisit only with thermal logging. |
| `ubatch-size` 128 / 256 vs 512 | Cold prefill dominates. | Cold-prefix time on the side server. |
| KV cache type q8_0 vs q4_0 vs f16 | q8_0 adds compute at 4096 ctx. | Gen and prefill tok/s per type. |
| `--slot-save-path` | A restart repeats the 76-101 s cold prefix. | Save, restart, time first request. |
| `--cache-reuse` | Partial prefix matches. | Vary the middle of the prompt, compare `cache_n`. |
| `--models-max 1` | Two mlocked models vs swap cost; check it does not evict the cache. | First-request latency after a model switch. |
| Shorter, stable system prompt and tool schema | Cold cost scales with prefix length. | Count prompt tokens of real clients. |
| Coder model slower than general | Cold prefix 101 s vs 76 s; gen 2.60 vs 3.24 tok/s with no draft. Cause unknown. | Compare template, sampling and flags. |
| JSON eval latency | 63 s avg for the 1.5B (report section 3). | Separate from prefix caching. |
| Fixed benchmark prompt set | Makes every change comparable. | Extend `src/` evals to use the server. |

## Invalid or untrusted results

| Item | Problem |
|---|---|
| All tok/s and cold-prefix comparisons from 2026-10-02 | Pi hit the soft temperature limit (`get_throttled` 0xe0008, 79.8-85.2 C) and has past under-voltage. Runs done back-to-back in fixed order are confounded. After the no-draft restart the cold prefix measured 110-123 s (general) and 122 s (coder) vs 76 / 101 s earlier, with identical prompts. |
| Old prompt-cache eval (0.82-1.26x, 0.0 ms) | `llama-cli` no longer accepts `--prompt-cache`; runs exited code 1. Replaced in `0178fb6`. |
| Report section 5, speculative 0.96 -> 1.37 tok/s (1.43x) | Baseline contradicts the 2.62 tok/s roofline figure for the same model; `llama-cli` harness, not the server. Re-run before trusting. |
| Server `timings` draft counters | This build exposes none; `draft_n` reads 0 in the sweep scripts. Use `llama-speculative` for acceptance. |

## Method notes

- Record `vcgencmd measure_temp` and `get_throttled` before and after every run; interleave A/B configs and cool down between runs.
- Side experiments run a separate `bin/llama-server` on port 8090 with the engine's flags; the live engine is not touched.
- Sweep scripts live in the session scratchpad and are not in the repo yet.
- Small samples (3 prompts x 96 tokens, one seed); treat differences under ~10% as noise.
