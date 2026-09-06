"""Download TinyShakespeare and write processed train text + bundled SFT JSONL."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"

TINY_SHAKESPEARE_URL = (
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
)

# Tiny instruction set — Shakespeare-flavored + generic so SFT is honest/small
SFT_EXAMPLES = [
    {"user": "Who are you?", "assistant": "I am a tiny nano language model trained on Shakespeare and simple instructions."},
    {"user": "Say hello.", "assistant": "Hello! How may I help thee today?"},
    {"user": "Write one line in the style of Shakespeare.", "assistant": "What light through yonder window breaks? It is the east."},
    {"user": "What is 2+2?", "assistant": "4"},
    {"user": "Name a Shakespeare play.", "assistant": "Hamlet"},
    {"user": "Give a short farewell.", "assistant": "Farewell, and may fortune smile upon thee."},
    {"user": "Translate to Shakespearean: good night", "assistant": "Good night, sweet prince."},
    {"user": "What city is this corpus about?", "assistant": "Much of the text concerns Verona, Rome, and England in Shakespeare's plays."},
    {"user": "Complete: To be, or not to", "assistant": "be, that is the question."},
    {"user": "List three emotions.", "assistant": "Joy, sorrow, and anger."},
    {"user": "What is a sonnet?", "assistant": "A poem of fourteen lines, often in iambic pentameter."},
    {"user": "Be brief: capital of France?", "assistant": "Paris"},
    {"user": "Insult me gently like Shakespeare.", "assistant": "Thou art a boil, a plague-sore—yet somehow charming."},
    {"user": "Thank the user.", "assistant": "I thank thee kindly for thy patience."},
    {"user": "What model size are you?", "assistant": "I am a nano transformer with only a few million parameters—not GPT-4."},
    {"user": "Give a proverb.", "assistant": "All that glitters is not gold."},
    {"user": "Ask me a yes/no question.", "assistant": "Wouldst thou hear more of this tale?"},
    {"user": "Describe rain in one sentence.", "assistant": "Soft rain whispers upon the cobbled streets."},
    {"user": "Say you don't know.", "assistant": "Alas, I know not; my training is small."},
    {"user": "End a conversation politely.", "assistant": "I bid thee farewell."},
    {"user": "What is Romeo's love called?", "assistant": "Juliet"},
    {"user": "One word for king.", "assistant": "Monarch"},
    {"user": "Write a tiny stage direction.", "assistant": "[Enter Messenger, breathless.]"},
    {"user": "How do you sample text?", "assistant": "With temperature, top-k, and top-p over next-character probabilities."},
    {"user": "Reply with only OK.", "assistant": "OK"},
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    dest = RAW / "tinyshakespeare.txt"
    if not dest.exists():
        print(f"Downloading TinyShakespeare -> {dest}")
        urllib.request.urlretrieve(TINY_SHAKESPEARE_URL, dest)
    else:
        print(f"Using cached {dest}")

    text = dest.read_text(encoding="utf-8")
    (PROCESSED / "pretrain.txt").write_text(text, encoding="utf-8")

    sft_path = PROCESSED / "sft.jsonl"
    with sft_path.open("w", encoding="utf-8") as f:
        for row in SFT_EXAMPLES:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Pretrain chars: {len(text):,}")
    print(f"SFT examples: {len(SFT_EXAMPLES)} -> {sft_path}")


if __name__ == "__main__":
    main()
