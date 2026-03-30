from __future__ import annotations

from enum import Enum


class StageName(str, Enum):
    INPUT = "input"
    AI = "ai"
    ACTION_APPLICATION = "action_application"
    PHYSICS = "physics"
    EVENT_PROCESSING = "event_processing"
    OBSERVATION_BUILD = "observation_build"
    RENDER_SNAPSHOT = "render_snapshot"


STAGE_ORDER = [
    StageName.INPUT,
    StageName.AI,
    StageName.ACTION_APPLICATION,
    StageName.PHYSICS,
    StageName.EVENT_PROCESSING,
    StageName.OBSERVATION_BUILD,
    StageName.RENDER_SNAPSHOT,
]
