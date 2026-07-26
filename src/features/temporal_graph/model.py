"""Temporal Graph Transformer for taxi zone demand forecasting."""
from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class TemporalGraphTransformerConfig:
    zone_count: int = 263
    history_steps: int = 48
    forecast_steps: int = 48
    hidden_dim: int = 128
    num_heads: int = 4
    num_layers: int = 3
    dropout: float = 0.1
    time_embed_dim: int = 32
    external_feat_dim: int = 0
    quantiles: tuple[float, ...] = (0.1, 0.5, 0.9)


class _GraphAttentionLayer(nn.Module):
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        assert self.head_dim * num_heads == hidden_dim
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, graph_bias: torch.Tensor | None = None) -> torch.Tensor:
        B, N, D = x.shape
        q = self.q_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        attn = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if graph_bias is not None:
            attn = attn + graph_bias.unsqueeze(0).unsqueeze(0)
        attn = torch.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        out = (attn @ v).transpose(1, 2).contiguous().view(B, N, -1)
        return self.out_proj(out)


class _TransformerBlock(nn.Module):
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.attention = _GraphAttentionLayer(hidden_dim, num_heads, dropout)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout),
        )
        self.norm2 = nn.LayerNorm(hidden_dim)

    def forward(self, x: torch.Tensor, graph_bias: torch.Tensor | None = None) -> torch.Tensor:
        x = x + self.attention(self.norm1(x), graph_bias)
        x = x + self.ffn(self.norm2(x))
        return x


class TemporalGraphTransformer(nn.Module):
    def __init__(self, config: TemporalGraphTransformerConfig):
        super().__init__()
        self.config = config
        self.max_input_dim = 1 + config.external_feat_dim
        self.input_proj = nn.Linear(self.max_input_dim, config.hidden_dim)
        self.zone_embed = nn.Embedding(config.zone_count, config.hidden_dim)
        self.time_embed = nn.Embedding(5000, config.hidden_dim)

        self.blocks = nn.ModuleList([
            _TransformerBlock(config.hidden_dim, config.num_heads, config.dropout)
            for _ in range(config.num_layers)
        ])
        self.temporal_pool = nn.AdaptiveAvgPool1d(1)
        self.quantile_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_dim // 2, config.forecast_steps),
            )
            for _ in config.quantiles
        ])
        self._graph_bias: torch.Tensor | None = None
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.5)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, std=0.02)

    def set_graph_bias(self, adjacency):
        bias = torch.as_tensor(adjacency, dtype=torch.float32)
        bias = torch.log1p(bias)
        bias = bias / (bias.max().clamp_min(1.0) + 1e-8) * 2.0 - 1.0
        bias = torch.where(bias < -0.99, -1e9, bias)
        self._graph_bias = bias

    def forward(self, demand_history, external_features=None):
        B, T, Z = demand_history.shape
        config = self.config

        demand = demand_history.unsqueeze(-1)
        if external_features is not None:
            if external_features.dim() == 3:
                ext = external_features.unsqueeze(2).expand(-1, -1, Z, -1)
            else:
                ext = external_features
            x = torch.cat([demand, ext], dim=-1)
        else:
            x = demand

        # Project input dimension to match model dimension
        # input_proj was built for demand+external_feat_dim, but may get demand-only
        in_feat = x.size(-1)
        weight = self.input_proj.weight[:, :in_feat]
        bias = self.input_proj.bias
        x = torch.nn.functional.linear(x, weight, bias)
        zone_ids = torch.arange(Z, device=x.device)
        x = x + self.zone_embed(zone_ids).unsqueeze(0).unsqueeze(0)

        x = x.view(B * T, Z, -1)
        time_ids = torch.arange(T, device=x.device).view(1, -1, 1).expand(B, -1, Z).reshape(B * T, Z)
        x = x + self.time_embed(time_ids % 5000)

        for block in self.blocks:
            x = block(x, self._graph_bias)

        x = x.view(B, T, Z, -1)
        x = x.permute(0, 2, 1, 3)
        x = x.reshape(B * Z, T, -1).permute(0, 2, 1)
        x = self.temporal_pool(x).squeeze(-1)
        x = x.view(B, Z, -1)

        # P50 is the median
        p50_raw = self.quantile_heads[1](x)  # index 1 = P50
        p50 = torch.nn.functional.softplus(p50_raw)

        if len(config.quantiles) >= 3:
            # P10: P50 - delta (delta >= 0 via softplus)
            delta_low = torch.nn.functional.softplus(self.quantile_heads[0](x))
            p10 = p50 - delta_low
            # P90: P50 + delta (delta >= 0 via softplus)
            delta_high = torch.nn.functional.softplus(self.quantile_heads[2](x))
            p90 = p50 + delta_high
        else:
            p10 = torch.nn.functional.softplus(self.quantile_heads[0](x))
            p90 = torch.nn.functional.softplus(self.quantile_heads[-1](x))

        outputs = {}
        if len(config.quantiles) >= 1:
            outputs["P10"] = p10
        if len(config.quantiles) >= 2:
            outputs["P50"] = p50
        if len(config.quantiles) >= 3:
            outputs["P90"] = p90
        return outputs

    @torch.no_grad()
    def predict(self, demand_history, external_features=None, *, device="cpu"):
        self.eval()
        demand_t = torch.as_tensor(demand_history, dtype=torch.float32, device=device).unsqueeze(0)
        ext_t = None
        if external_features is not None:
            ext_t = torch.as_tensor(external_features, dtype=torch.float32, device=device).unsqueeze(0)
        outputs = self.forward(demand_t, ext_t)
        return {k: v.squeeze(0).cpu().numpy() for k, v in outputs.items()}


def quantile_loss(predictions, targets, quantiles):
    losses = []
    for key, q in zip(("P10", "P50", "P90"), quantiles):
        pred = predictions[key]
        error = targets - pred
        loss = torch.max(q * error, (q - 1.0) * error)
        losses.append(loss.mean())
    return torch.stack(losses).mean()
