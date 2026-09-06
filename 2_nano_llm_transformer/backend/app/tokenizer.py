"""Character-level tokenizer with special tokens for chat/SFT."""

from __future__ import annotations

import json
from pathlib import Path

SPECIAL = {
    "<pad>": 0,
    "<unk>": 1,
    "<bos>": 2,
    "<eos>": 3,
    "<user>": 4,
    "<assistant>": 5,
}


class CharTokenizer:
    def __init__(self, chars: list[str]):
        self.special = dict(SPECIAL)
        # Reserve special ids; printable corpus chars follow
        self.id_to_token = [None] * len(SPECIAL)
        for tok, idx in SPECIAL.items():
            self.id_to_token[idx] = tok
        for ch in sorted(set(chars)):
            if ch not in SPECIAL:
                self.id_to_token.append(ch)
        self.token_to_id = {t: i for i, t in enumerate(self.id_to_token) if t is not None}
        self.vocab_size = len(self.id_to_token)

    @property
    def pad_id(self) -> int:
        return self.special["<pad>"]

    @property
    def bos_id(self) -> int:
        return self.special["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.special["<eos>"]

    @property
    def user_id(self) -> int:
        return self.special["<user>"]

    @property
    def assistant_id(self) -> int:
        return self.special["<assistant>"]

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        ids: list[int] = []
        if add_bos:
            ids.append(self.bos_id)
        unk = self.special["<unk>"]
        for ch in text:
            ids.append(self.token_to_id.get(ch, unk))
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: list[int] | list) -> str:
        out = []
        special_vals = set(self.special.values())
        for i in ids:
            if i in special_vals:
                continue
            if 0 <= i < len(self.id_to_token):
                tok = self.id_to_token[i]
                if tok is not None:
                    out.append(tok)
        return "".join(out)

    def format_chat(self, user: str, assistant: str | None = None) -> list[int]:
        ids = [self.bos_id, self.user_id] + self.encode(user) + [self.assistant_id]
        if assistant is not None:
            ids += self.encode(assistant) + [self.eos_id]
        return ids

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps({"chars": [t for t in self.id_to_token if t and t not in SPECIAL]}, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> CharTokenizer:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data["chars"])

    @classmethod
    def from_text(cls, text: str) -> CharTokenizer:
        return cls(list(text))
