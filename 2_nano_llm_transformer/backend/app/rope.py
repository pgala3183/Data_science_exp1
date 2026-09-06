"""Rotary Position Embeddings (RoPE)."""

from __future__ import annotations

import torch


def build_rope_cache(
    seq_len: int, head_dim: int, device: torch.device, base: float = 10000.0
) -> tuple[torch.Tensor, torch.Tensor]:
    assert head_dim % 2 == 0
    half = head_dim // 2
    inv_freq = 1.0 / (base ** (torch.arange(0, half, device=device).float() / half))
    t = torch.arange(seq_len, device=device).float()
    freqs = torch.outer(t, inv_freq)  # (T, half)
    cos = torch.cos(freqs)[None, None, :, :]  # (1,1,T,half)
    sin = torch.sin(freqs)[None, None, :, :]
    return cos, sin


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """
    x: (B, n_head, T, head_dim)
    cos/sin: (1, 1, T, head_dim/2) broadcastable
    """
    x1 = x[..., ::2]
    x2 = x[..., 1::2]
    # rotate pairs
    rot = torch.stack((-x2, x1), dim=-1).flatten(-2)
    # Interleave cos/sin to full dim
    cos_full = torch.repeat_interleave(cos, 2, dim=-1)
    sin_full = torch.repeat_interleave(sin, 2, dim=-1)
    t = x.size(-2)
    return x * cos_full[:, :, :t] + rot * sin_full[:, :, :t]
