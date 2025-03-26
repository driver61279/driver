"""The tracks.ini file contains track metadata.
"""

from dataclasses import dataclass
from typing import Optional
import enum
import re
import os


class StageSurface(enum.Enum):
    TARMAC = 0
    GRAVEL = 1
    SNOW = 2

    def pretty(self) -> str:
        return self.name.title()


def sanitise_stage_name(name: str) -> str:
    return re.sub("[^0-9a-zA-Z]", "-", name)


@dataclass
class TracksINI:
    track_id: int
    track_dir: str
    particles: str
    stage_name: str
    surface: StageSurface
    length: float
    author: str
    country_code: str
    splash_screen_path: Optional[str] = None

    def serialise(self) -> str:
        lines = []
        lines.append(f"[Map{self.track_id}]")
        track_name = os.path.join(self.track_dir, f"track-{self.track_id}")
        lines.append(f'TrackName="{track_name}"')
        lines.append(f'Particles="Maps\\{self.particles}"')
        lines.append(f'StageName="{self.stage_name}"')
        lines.append(f"Surface={self.surface.value}")
        lines.append(f"Length={round(self.length, 1):.1f}")
        lines.append(f"Author={self.author}")
        lines.append(f"CountryCode={self.country_code}")
        if self.splash_screen_path is not None:
            lines.append(f'SplashScreen="{self.splash_screen_path}"')
        return "\n".join(lines)
