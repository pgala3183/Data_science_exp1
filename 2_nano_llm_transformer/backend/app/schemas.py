from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    temperature: float = Field(0.9, ge=0.05, le=2.0)
    max_tokens: int = Field(120, ge=1, le=512)
    top_k: int = Field(40, ge=0, le=200)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    chat: bool = Field(
        True,
        description="If true, wrap prompt as <|user|>...<|assistant|> for SFT-style generation",
    )


class ModelInfo(BaseModel):
    params: int
    checkpoint: str
    stage: str | None
    config: dict
    meta: dict
