# Open WebUI (multi-model chat)

Self-hosted chat UI wired to [OpenRouter](https://openrouter.ai) (hundreds of models
behind one key) and, optionally, local models through [Ollama](https://ollama.com).

## Run

Requires Docker.

```bash
cd open-webui
cp .env.example .env        # then paste your OpenRouter key into .env
docker compose up -d
```

Open http://localhost:3000. The first account you create becomes the admin.
Pick any OpenRouter model from the model dropdown.

## Local models (optional)

```bash
ollama pull qwen3:8b
ollama serve
```

Ollama models appear in the same dropdown automatically.

## Manage

```bash
docker compose pull && docker compose up -d   # update
docker compose down                            # stop (chats are kept in the volume)
```

To change the key later, edit `.env` and run `docker compose up -d`, or set it under
Admin Settings → Connections.
