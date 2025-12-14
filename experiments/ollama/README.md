# Ollama with Phi-3

Stateless Ollama REST API service running Phi-3 Mini (3.8B parameters, Q4_0 quantized) for the experiments namespace.

## Architecture

- **Single instance** deployment due to GPU constraints
- **GPU accelerated** via NVIDIA RuntimeClass (GTX 960, 4GB VRAM)
- **Persistent model storage** via hostPath volume
- **Init container** pulls Phi-3 model on first startup

## Service Details

| Property | Value |
|----------|-------|
| Service | `ollama.experiments.svc.cluster.local` |
| Port | `11434` |
| Model | `phi3:latest` (2.2GB) |
| GPU | NVIDIA GeForce GTX 960 |

## Endpoints

### Health Check
```
GET /
```

### List Models
```
GET /api/tags
```

### Chat Completion (Stateless)
```
POST /api/chat
```

### Generate (Single prompt)
```
POST /api/generate
```

## Example API Calls

### Chat Completion
```bash
curl -X POST http://ollama.experiments:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3",
    "messages": [
      {"role": "user", "content": "What is Kubernetes?"}
    ],
    "stream": false
  }'
```

Response:
```json
{
  "model": "phi3",
  "message": {
    "role": "assistant",
    "content": "Kubernetes is an open-source container orchestration platform..."
  },
  "done": true
}
```

### Multi-turn Conversation
```bash
curl -X POST http://ollama.experiments:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3",
    "messages": [
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "Python is a programming language."},
      {"role": "user", "content": "What are its main uses?"}
    ],
    "stream": false
  }'
```

### Generate (Simple)
```bash
curl -X POST http://ollama.experiments:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3",
    "prompt": "Write a haiku about containers",
    "stream": false
  }'
```

### List Available Models
```bash
curl http://ollama.experiments:11434/api/tags
```

### With Options (Temperature, etc.)
```bash
curl -X POST http://ollama.experiments:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3",
    "messages": [
      {"role": "user", "content": "Tell me a joke"}
    ],
    "stream": false,
    "options": {
      "temperature": 0.9,
      "top_p": 0.9
    }
  }'
```

## Testing from Within Cluster

```bash
kubectl run curl-test --image=curlimages/curl -n experiments --rm -it --restart=Never -- \
  curl -s http://ollama:11434/api/tags
```

## Resource Usage

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 250m | 4000m |
| Memory | 512Mi | 8Gi |
| GPU | 1 | 1 |

Model memory footprint on GPU:
- Weights: ~1.7 GiB
- KV Cache: ~1.3 GiB
- Compute: ~256 MiB
