from __future__ import annotations


def resolve_device(device_name: str) -> str:
    import torch

    normalized = device_name.strip().lower()
    if normalized == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if normalized.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"CUDA was requested explicitly, but no CUDA device is available: {device_name}")
    return device_name


def resolve_torch_dtype(device_name: str):
    import torch

    if device_name.startswith("cuda"):
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32
