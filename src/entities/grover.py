from typing import Optional  # Optional is clearer in older Python versions

from pydantic import BaseModel


class GroverConfig(BaseModel):
    marked_state: str  # for one marked state
    iteration: Optional[str] = None  # default: optimal iterations int(pi/4 sqrt(2^n))
