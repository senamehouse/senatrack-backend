from typing import Any


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


try:
    # Pydantic v2
    from pydantic import BaseModel  # type: ignore
    from pydantic.config import ConfigDict  # type: ignore

    class BaseCamelModel(BaseModel):
        """Base model that outputs camelCase JSON while keeping snake_case in Python."""

        model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

except Exception:  # pragma: no cover - fallback for pydantic v1
    # Pydantic v1 fallback
    from pydantic import BaseModel  # type: ignore

    class BaseCamelModel(BaseModel):
        """Base model that outputs camelCase JSON while keeping snake_case in Python."""

        class Config:
            alias_generator = to_camel
            allow_population_by_field_name = True





