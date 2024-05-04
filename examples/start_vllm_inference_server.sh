#!/bin/bash

# this is the same port ollama openai api binds to, don't run them together or change the port
python -m vllm.entrypoints.openai.api_server \
    --host 127.0.0.1 \
    --port 11434 \
    --model NousResearch/Hermes-2-Pro-Llama-3-8B
