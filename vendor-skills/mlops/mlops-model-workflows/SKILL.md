---
name: mlops-model-workflows
description: "Use when working with ML/LLM tooling: Hugging Face Hub, local/served inference, evaluation harnesses, W&B, DSPy, model surgery, audio/image models, and benchmark/experiment workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mlops, llm, inference, evaluation, huggingface, wandb, dspy]
    related_skills: []
---

# MLOps & Model Workflows

## Overview

Umbrella for model discovery, evaluation, inference serving, experiment tracking, prompt-program optimization, and specialized ML model workflows. Always record exact model IDs, revisions, commands, datasets, and hardware/runtime constraints.

## When to Use

- Hugging Face model/dataset search, download, upload.
- llama.cpp/GGUF local inference or server usage.
- vLLM/high-throughput serving.
- lm-eval-harness benchmarks.
- Weights & Biases logging/sweeps/artifacts.
- DSPy prompt/RAG optimization.
- Abliteration/refusal analysis, SAM segmentation, AudioCraft generation.

## Workflow

1. Define task: download, serve, evaluate, track, optimize, or transform.
2. Check hardware, disk, Python/CUDA versions, and credentials.
3. Pin exact model/dataset/revision and command parameters.
4. Run a small smoke test before long jobs.
5. Capture metrics/logs/artifacts and verify outputs.

## Subdomains

### Inference

For llama.cpp/vLLM, match quantization/model size to hardware. Expose health endpoints and run a real prompt test.

### Evaluation and Tracking

For lm-eval/W&B, log dataset versions, seeds, and config. Avoid comparing runs with different prompts/tokenizers without noting it.

### Hub and Model Assets

Use `hf`/API safely; never print tokens. Verify downloads with file sizes/checksums when needed.

### Research/Optimization

DSPy and model-surgery workflows need baseline metrics before optimization and post-change comparisons.

## Pitfalls

- Reporting benchmark numbers without command/config/dataset.
- Starting large downloads without disk checks.
- Confusing model family names with exact revisions.
- Assuming GPU availability from memory rather than probing live system.

## Verification Checklist

- [ ] Environment/hardware checked.
- [ ] Exact model/dataset/revision recorded.
- [ ] Smoke test or benchmark run completed.
- [ ] Metrics/artifacts saved or reported.
