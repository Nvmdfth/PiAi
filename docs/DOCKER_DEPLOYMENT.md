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

* `cpuset: "0-2"`: Dedicates physical CPU cores 0, 1, and 2 to LLM matrix computation while reserving core 3 for host system processes and Docker daemon networking.
* `ulimits.memlock: -1`: Bypasses default 64KB memory lock ceilings so `--mlock` can pin model weights directly into physical RAM.
* `volumes`: GGUF weights are mounted from the host filesystem directly, enabling kernel zero-copy memory mapping (`mmap`).
