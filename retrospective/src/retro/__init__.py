"""Retrospective analysis of the ViPharmind history (read-only, pinned commits)."""

from pathlib import Path

MAIN_SHA = "3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe"
CAMERA_READY_SHA = "61d10db85f0f4d9cb871e8fff89ce06e2c49b930"
PINNED_REVS = (MAIN_SHA, CAMERA_READY_SHA)
DEFAULT_REPO = Path.home() / "personal" / "vipharmind-camera-ready"
