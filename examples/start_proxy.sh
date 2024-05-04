#!/bin/bash

cd .. && uvicorn openai_api_tool_proxy:app --reload --port 8001