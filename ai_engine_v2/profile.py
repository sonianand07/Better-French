from __future__ import annotations
"""User profile schema and helpers.
Store each profile as simple JSON in `profiles/<user_id>.json`.
"""
import json, pathlib
from typing import List
from pydantic import BaseModel, Field

PROFILES_DIR = pathlib.Path(__file__).resolve().parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)

class UserProfile(BaseModel):
    user_id: str = Field(..., min_length=1)
    native_lang: str = "en"
    french_level: str = "B1"  # CEFR A1-C2
    lives_in: str = ""
    work_domains: List[str] = []
    pain_points: List[str] = []
    interests: List[str] = []

    # --------------------------------------------------------- helpers
    @classmethod
    def load(cls, path_or_user: str | pathlib.Path):
        path = pathlib.Path(path_or_user)
        if not path.suffix:
            path = PROFILES_DIR / f"{path_or_user}.json"
        data = json.loads(path.read_text())
        return cls.parse_obj(data)

    def save(self):
        path = PROFILES_DIR / f"{self.user_id}.json"
        path.write_text(self.json(indent=2, ensure_ascii=False))
        return path 