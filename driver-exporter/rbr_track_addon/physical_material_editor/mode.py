from abc import abstractmethod
from typing import List, Set, Tuple

import bpy  # type: ignore

from .properties import RBRFallbackMaterials


class Editor:
    """Interface for the main editor class."""

    @property
    def material_maps(self) -> bpy.types.Collection:  # [RBRMaterialMaps]
        """Get the currently active material maps."""
        raise NotImplementedError

    @property
    def fallback_materials(self) -> RBRFallbackMaterials:
        """Get the fallback materials"""
        raise NotImplementedError

    # Mode switching functions
    def to_overview_mode(self) -> None:
        raise NotImplementedError

    def to_resize_mode(self, resizing_index: int) -> None:
        raise NotImplementedError

    def to_edit_mode(self, editing_index: int) -> None:
        raise NotImplementedError

    def to_new_mode(self) -> None:
        raise NotImplementedError

    def last_mouse_region(self) -> Tuple[bpy.types.Region, float, float]:
        """Get the last hovered region and mouse position within that region, in
        region space."""
        raise NotImplementedError

    def hovered_map_indices(self) -> List[int]:
        """Which maps are currently being hovered over?"""
        raise NotImplementedError

    # TODO this is overwritten by the status bar.
    def report(self, level: Set[str], message: str) -> None:
        """A passthrough for operator report"""
        raise NotImplementedError


class Mode:
    def draw(
        self,
        editor: Editor,
        region: bpy.types.Region,
    ) -> None:
        pass

    @abstractmethod
    def handle_event(
        self,
        editor: Editor,
        event: bpy.types.Event,
    ) -> Set[str]:
        pass

    def cursor(self) -> str:
        return "DEFAULT"

    def messages(self, editor: Editor) -> List[str]:
        """Text which is displayed in the lower left corner of the screen."""
        return []

    def draw_status(self, ui: bpy.types.UILayout) -> None:
        """Draw to the workspace status. Should be used for contextual controls."""
        pass
