# Pydantic Schemas
from pydantic import ConfigDict

# Shared configuration for all schemas
SCHEMA_CONFIG = ConfigDict(
    populate_by_name=True,
    from_attributes=True,
    serialize_by_alias=True
)

