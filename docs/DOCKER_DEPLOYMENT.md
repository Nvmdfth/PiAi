# Docker Deployment Guide for Raspberry Pi

This guide outlines containerized deployment of `llama-server` on Raspberry Pi 4 and Raspberry Pi 5 with zero performance degradation.

---

## 1. Quick Start

### Build and Launch on Raspberry Pi 4:
```bash
docker compose --profile pi4 up -d --build
```

### Build and Launch on Raspberry Pi 5:
```bash
docker compose --profile pi5 up -d --build
```

---

## 2. Testing the OpenAI-Compatible Endpoint

Once running, the container serves standard OpenAI completions and chat endpoints on `http://localhost:8080/v1`:

### Health Check:
```bash
curl http://localhost:8080/health
```

### Chat Completion:
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "system", "content": "You are a concise edge assistant."},
      {"role": "user", "content": "What is the CPU architecture of a Raspberry Pi 5?"}
    ],
    "temperature": 0.2
  }'
```

### Structured Tool Calling with GBNF Grammar:
```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "<|im_start|>system\nYou are a dispatcher.<|im_end|>\n<|im_start|>user\nRestart worker node 2<|im_end|>\n<|im_start|>assistant\n",
    "grammar": "'"$(cat grammars/tool_call.gbnf | tr '\n' ' ')"'",
    "n_predict": 128
  }'
```

---

## 3. Key Production Tuning in `docker-compose.yml`

* `cpuset: "0-3"`: Pins the container to all four cores; the presets use 3 generation threads and 4 batch threads.
* `ulimits.memlock: -1`: Bypasses default 64KB memory lock ceilings so `--mlock` can pin model weights directly into physical RAM.
* `volumes`: GGUF weights are mounted from the host filesystem directly, enabling kernel zero-copy memory mapping (`mmap`).
* `./slot_cache:/slots` + `slot-save-path = /slots` (in each preset): holds saved KV caches so a restart does not repeat the cold prefix (80-100 s for ~440 tokens on a Pi 4).

## 4. Slot Cache Persistence

`docker/entrypoint.sh` (bind-mounted over the image copy, so no rebuild is needed) manages the cache:

* **Restore on start**: once `/health` is ok, each saved cache is restored. This also loads the models.
* **Save on stop**: on SIGTERM (`docker compose stop/restart`) the busiest slot of every loaded model is saved.
* **Periodic save**: every `SLOT_SAVE_INTERVAL` seconds (default `600`, `0` disables) so a crash keeps recent work. Busy models and unchanged slots are skipped.
* **Stale guard**: each cache is stored with a fingerprint of the model file and the preset. Any preset edit or model change makes it skip the restore; the cache is rebuilt on use.
* Files live in `slot_cache/` (git-ignored): `<model>.bin`, `.meta` (fingerprint), `.key` (change marker). Deleting them is safe.
* Limits: one slot per model, graceful stops and periodic saves only (work newer than the last save is lost on a crash).
