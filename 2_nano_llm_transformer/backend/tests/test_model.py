import torch

from app.config import NanoConfig
from app.model import NanoTransformer
from app.rope import apply_rope, build_rope_cache
from app.tokenizer import CharTokenizer


def test_tokenizer_roundtrip():
    tok = CharTokenizer.from_text("Hello Shakespeare!\n")
    ids = tok.encode("Hello")
    assert tok.decode(ids) == "Hello"
    chat = tok.format_chat("Hi", "Yo")
    assert tok.user_id in chat and tok.assistant_id in chat


def test_rope_shapes():
    cos, sin = build_rope_cache(16, 32, torch.device("cpu"))
    x = torch.randn(2, 4, 16, 32)
    y = apply_rope(x, cos, sin)
    assert y.shape == x.shape


def test_model_forward_and_params():
    config = NanoConfig(vocab_size=64, block_size=32, n_layer=2, n_head=4, n_embd=64)
    model = NanoTransformer(config)
    assert model.param_count() > 10_000
    idx = torch.randint(0, 64, (2, 16))
    targets = torch.randint(0, 64, (2, 16))
    logits, loss = model(idx, targets)
    assert logits.shape == (2, 16, 64)
    assert loss is not None
    loss.backward()


def test_generate_yields_tokens():
    config = NanoConfig(vocab_size=40, block_size=32, n_layer=1, n_head=2, n_embd=32)
    model = NanoTransformer(config)
    idx = torch.zeros((1, 4), dtype=torch.long)
    tokens = []
    for tid, _ in model.generate(idx, max_new_tokens=5, temperature=1.0, top_k=10, top_p=0.95):
        tokens.append(tid)
    assert len(tokens) == 5
