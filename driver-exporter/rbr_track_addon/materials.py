"""
Physical material hierarchy:

    Road surfaces
        Gravel
            Fine/Medium/Coarse
                Shallow/Deep/Deeper
                    Wet/Damp/Dry
        Tarmac
            Fine/Medium/Coarse
                Clean/Sprinkled/Covered
                    Wet/Damp/Dry
        Snow
            Snow on gravel
                Shallow/Medium/Deep
            Snow on ice
                Shallow/Medium/Deep
            Snowwall Bottom
        Cobble
            Dry/Damp/Wet

    Ground surfaces
        Water surface
        Grass
            Hard/Medium/Soft
                Wet/Damp/Dry
        Rough
            Rough/Very Rough
                Dry/Damp/Wet
        Dirt
            Hard/Medium/Soft
                Dry/Damp/Wet

    Roadside scenery
        Trees
            Small/Medium/Large
            Stump
            Bendable
            Trunk
                Small/Medium/Large
        Rock
            Small/Medium/Large
        Metal Pole
        Metal Barrier
"""

import bpy  # type: ignore

from dataclasses import dataclass

from rbr_track_formats import errors
from rbr_track_formats.mat import MaterialID


class RBRMaterialPicker(bpy.types.PropertyGroup):
    def init(self, context: bpy.types.Context) -> None:
        self.__update__(context)

    # Control the alpha level of the material map
    alpha: bpy.props.FloatProperty(  # type: ignore
        name="Alpha",  # noqa: F821
        min=0,
        max=1,
        default=0.4,
    )

    def set_material_id(self, material_id: MaterialID) -> bool:
        is_supported = self.set_from_material_id(material_id)
        if is_supported:
            if self.to_material_id() is not material_id:
                raise errors.RBRAddonBug("Failed to set material ID")
            self.material_id = material_id.value
            return True
        else:
            return False

    material_id: bpy.props.IntProperty(  # type: ignore
        name="Material ID",
    )

    def __update__(self, context: bpy.types.Context) -> None:
        self.material_id = self.to_material_id().value

    category: bpy.props.EnumProperty(  # type: ignore
        name="Category",  # noqa: F821
        items=[
            ("ROAD", "Road", "", 0),  # noqa: F821
            ("GROUND", "Ground", "", 1),  # noqa: F821
            ("PASSTHROUGH", "Passthrough", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    road_surface: bpy.props.EnumProperty(  # type: ignore
        name="Road Surface",
        items=[
            ("TARMAC", "Tarmac", "", 0),  # noqa: F821
            ("GRAVEL", "Gravel", "", 1),  # noqa: F821
            ("SNOW", "Snow", "", 2),  # noqa: F821
            ("COBBLE", "Cobble", "", 3),  # noqa: F821
        ],
        update=__update__,
    )

    wetness: bpy.props.EnumProperty(  # type: ignore
        name="Wetness",  # noqa: F821
        items=[
            ("DRY", "Dry", "", 0),  # noqa: F821
            ("DAMP", "Damp", "", 1),  # noqa: F821
            ("WET", "Wet", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    gravel_type: bpy.props.EnumProperty(  # type: ignore
        name="Gravel Type",
        items=[
            ("US", "US", "", 0),  # noqa: F821
            ("FINE", "Fine", "", 1),  # noqa: F821
            ("MEDIUM", "Medium", "", 2),  # noqa: F821
            ("COARSE", "Coarse", "", 3),  # noqa: F821
            ("BR", "British", "", 4),  # noqa: F821
        ],
        update=__update__,
    )

    gravel_depth: bpy.props.EnumProperty(  # type: ignore
        name="Gravel Depth",
        items=[
            ("SHALLOW", "Shallow", "", 0),  # noqa: F821
            ("DEEP", "Deep", "", 1),  # noqa: F821
            ("DEEPER", "Deeper", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    tarmac_type: bpy.props.EnumProperty(  # type: ignore
        name="Tarmac Type",
        items=[
            ("FINE", "Fine", "", 0),  # noqa: F821
            ("MEDIUM", "Medium", "", 1),  # noqa: F821
            ("COARSE", "Coarse", "", 2),  # noqa: F821
            ("BLACK_ICE", "Black Ice", "", 3),  # noqa: F821
        ],
        update=__update__,
    )

    tarmac_cleanliness: bpy.props.EnumProperty(  # type: ignore
        name="Tarmac Cleanliness",
        items=[
            ("CLEAN", "Clean", "", 0),  # noqa: F821
            ("SPRINKLED", "Sprinkled", "", 1),  # noqa: F821
            ("COVERED", "Covered", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    cobble_type: bpy.props.EnumProperty(  # type: ignore
        name="Cobble Type",
        items=[
            ("COBBLE", "Cobble", "", 0),  # noqa: F821
            ("SETT", "Sett", "", 1),  # noqa: F821
        ],
        update=__update__,
    )

    snow_subsurface: bpy.props.EnumProperty(  # type: ignore
        name="Snow Subsurface",
        items=[
            ("GRAVEL", "Gravel", "Snow on Gravel", 0),  # noqa: F821
            ("ICE", "Ice", "Snow on Ice", 1),  # noqa: F821
            ("BANK", "Snowbank", "Snowbank Base", 2),  # noqa: F821
        ],
        update=__update__,
    )

    snow_depth: bpy.props.EnumProperty(  # type: ignore
        name="Snow Depth",
        items=[
            ("SHALLOW", "Shallow", "", 0),  # noqa: F821
            ("MEDIUM", "Medium", "", 1),  # noqa: F821
            ("DEEP", "Deep", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    ground_surface: bpy.props.EnumProperty(  # type: ignore
        name="Ground Surface",
        items=[
            ("WATER", "Water", "", 0),  # noqa: F821
            ("GRASS", "Grass", "", 1),  # noqa: F821
            ("ROUGH", "Rough", "", 2),  # noqa: F821
            ("DIRT", "Dirt", "", 3),  # noqa: F821
        ],
        update=__update__,
    )

    hardness: bpy.props.EnumProperty(  # type: ignore
        name="Hardness",  # noqa: F821
        items=[
            ("HARD", "Hard", "", 0),  # noqa: F821
            ("MEDIUM", "Medium", "", 1),  # noqa: F821
            ("SOFT", "Soft", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    rough_type: bpy.props.EnumProperty(  # type: ignore
        name="Rough Type",
        items=[
            ("ROUGH", "Rough", "", 0),  # noqa: F821
            ("VERYROUGH", "Very Rough", "", 1),  # noqa: F821
        ],
        update=__update__,
    )

    scenery_type: bpy.props.EnumProperty(  # type: ignore
        name="Scenery Type",
        items=[
            ("TREE", "Tree", "", 0),  # noqa: F821
            ("ROCK", "Rock", "", 1),  # noqa: F821
            ("METAL", "Metal", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    tree_type: bpy.props.EnumProperty(  # type: ignore
        name="Tree Type",
        items=[
            ("TREE", "Tree", "", 0),  # noqa: F821
            ("STUMP", "Tree Stump", "", 1),  # noqa: F821
            ("TRUNK", "Tree Trunk", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    tree_size: bpy.props.EnumProperty(  # type: ignore
        name="Tree Size",
        items=[
            ("BENDABLE", "Bendable", "", 0),  # noqa: F821
            ("SMALL", "Small", "", 1),  # noqa: F821
            ("MEDIUM", "Medium", "", 2),  # noqa: F821
            ("LARGE", "Large", "", 3),  # noqa: F821
        ],
        update=__update__,
    )

    tree_trunk_size: bpy.props.EnumProperty(  # type: ignore
        name="Tree Trunk Size",
        items=[
            ("SMALL", "Small", "", 0),  # noqa: F821
            ("MEDIUM", "Medium", "", 1),  # noqa: F821
            ("LARGE", "Large", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    rock_size: bpy.props.EnumProperty(  # type: ignore
        name="Rock Size",
        items=[
            ("SMALL", "Small", "", 0),  # noqa: F821
            ("MEDIUM", "Medium", "", 1),  # noqa: F821
            ("LARGE", "Large", "", 2),  # noqa: F821
        ],
        update=__update__,
    )

    metal_type: bpy.props.EnumProperty(  # type: ignore
        name="Metal Type",
        items=[
            ("METAL_POLE", "Metal Pole", "", 0),  # noqa: F821
            ("METAL_BARRIER", "Metal Barrier", "", 1),  # noqa: F821
        ],
        update=__update__,
    )

    def draw(self, context: bpy.types.Context, ui: bpy.types.UILayout) -> None:
        ui.prop(self, "category", expand=True)
        ui.separator(factor=0.5)
        if self.category == "ROAD":
            ui.prop(self, "road_surface", expand=True)
            ui.separator(factor=0.5)
            if self.road_surface == "TARMAC":
                ui.prop(self, "tarmac_type", expand=True)
                if self.tarmac_type != "BLACK_ICE":
                    ui.prop(self, "tarmac_cleanliness", expand=True)
                    ui.prop(self, "wetness", expand=True)
            elif self.road_surface == "GRAVEL":
                ui.prop(self, "gravel_type", expand=True)
                ui.prop(self, "gravel_depth", expand=True)
                ui.prop(self, "wetness", expand=True)
            elif self.road_surface == "SNOW":
                ui.prop(self, "snow_subsurface", expand=True)
                if self.snow_subsurface != "BANK":
                    ui.prop(self, "snow_depth", expand=True)
            elif self.road_surface == "COBBLE":
                ui.prop(self, "cobble_type", expand=True)
                ui.prop(self, "wetness", expand=True)
        elif self.category == "GROUND":
            ui.prop(self, "ground_surface", expand=True)
            ui.separator(factor=0.5)
            if self.ground_surface == "WATER":
                pass
            elif self.ground_surface == "GRASS":
                ui.prop(self, "hardness", expand=True)
                ui.prop(self, "wetness", expand=True)
            elif self.ground_surface == "ROUGH":
                ui.prop(self, "rough_type", expand=True)
                ui.prop(self, "wetness", expand=True)
            elif self.ground_surface == "DIRT":
                ui.prop(self, "hardness", expand=True)
                ui.prop(self, "wetness", expand=True)
        elif self.category == "PASSTHROUGH":
            pass

    def set_from_material_id(self, raw_material_id: MaterialID) -> bool:
        material_id = raw_material_id.simplify()
        if material_id is MaterialID.TARMAC_FINE_CLEAN_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_FINE_CLEAN_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_FINE_CLEAN_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_FINE_SPRINKLED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_FINE_SPRINKLED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_FINE_SPRINKLED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_FINE_COVERED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_FINE_COVERED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_FINE_COVERED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "FINE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "WET"

        elif material_id is MaterialID.TARMAC_MEDIUM_CLEAN_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_MEDIUM_CLEAN_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_MEDIUM_CLEAN_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_MEDIUM_SPRINKLED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_MEDIUM_SPRINKLED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_MEDIUM_SPRINKLED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_MEDIUM_COVERED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_MEDIUM_COVERED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_MEDIUM_COVERED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "MEDIUM"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "WET"

        elif material_id is MaterialID.TARMAC_COARSE_CLEAN_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_COARSE_CLEAN_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_COARSE_CLEAN_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "CLEAN"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_COARSE_SPRINKLED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_COARSE_SPRINKLED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_COARSE_SPRINKLED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "SPRINKLED"
            self.wetness = "WET"
        elif material_id is MaterialID.TARMAC_COARSE_COVERED_DRY:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DRY"
        elif material_id is MaterialID.TARMAC_COARSE_COVERED_DAMP:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "DAMP"
        elif material_id is MaterialID.TARMAC_COARSE_COVERED_WET:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "COARSE"
            self.tarmac_cleanliness = "COVERED"
            self.wetness = "WET"

        if material_id is MaterialID.BLACK_ICE:
            self.category = "ROAD"
            self.road_surface = "TARMAC"
            self.tarmac_type = "BLACK_ICE"

        elif material_id is MaterialID.US_GRAVEL_FINE_SHALLOW_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DRY"
        elif material_id is MaterialID.US_GRAVEL_FINE_SHALLOW_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DAMP"
        elif material_id is MaterialID.US_GRAVEL_FINE_SHALLOW_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "SHALLOW"
            self.wetness = "WET"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEP_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEP"
            self.wetness = "DRY"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEP_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEP"
            self.wetness = "DAMP"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEP_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEP"
            self.wetness = "WET"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEPER_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEPER"
            self.wetness = "DRY"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEPER_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEPER"
            self.wetness = "DAMP"
        elif material_id is MaterialID.US_GRAVEL_FINE_DEEPER_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "US"
            self.gravel_depth = "DEEPER"
            self.wetness = "WET"

        elif material_id is MaterialID.GRAVEL_FINE_SHALLOW_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_FINE_SHALLOW_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_FINE_SHALLOW_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_FINE_DEEP_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEP"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_FINE_DEEP_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEP"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_FINE_DEEP_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEP"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_FINE_DEEPER_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEPER"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_FINE_DEEPER_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEPER"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_FINE_DEEPER_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "FINE"
            self.gravel_depth = "DEEPER"
            self.wetness = "WET"

        elif material_id is MaterialID.GRAVEL_MEDIUM_SHALLOW_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_MEDIUM_SHALLOW_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_MEDIUM_SHALLOW_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "SHALLOW"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEP_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEP"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEP_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEP"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEP_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEP"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEPER_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEPER"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEPER_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEPER"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_MEDIUM_DEEPER_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "MEDIUM"
            self.gravel_depth = "DEEPER"
            self.wetness = "WET"

        elif material_id is MaterialID.GRAVEL_COARSE_SHALLOW_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_COARSE_SHALLOW_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_COARSE_SHALLOW_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "SHALLOW"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEP_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEP"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEP_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEP"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEP_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEP"
            self.wetness = "WET"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEPER_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEPER"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEPER_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEPER"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRAVEL_COARSE_DEEPER_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "COARSE"
            self.gravel_depth = "DEEPER"
            self.wetness = "WET"

        elif material_id is MaterialID.BR_GRAVEL_COARSE_SHALLOW_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DRY"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_SHALLOW_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "SHALLOW"
            self.wetness = "DAMP"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_SHALLOW_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "SHALLOW"
            self.wetness = "WET"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEP_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEP"
            self.wetness = "DRY"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEP_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEP"
            self.wetness = "DAMP"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEP_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEP"
            self.wetness = "WET"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEPER_DRY:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEPER"
            self.wetness = "DRY"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEPER_DAMP:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEPER"
            self.wetness = "DAMP"
        elif material_id is MaterialID.BR_GRAVEL_COARSE_DEEPER_WET:
            self.category = "ROAD"
            self.road_surface = "GRAVEL"
            self.gravel_type = "BR"
            self.gravel_depth = "DEEPER"
            self.wetness = "WET"

        elif material_id is MaterialID.SNOWONGRAVEL_SHALLOW:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "GRAVEL"
            self.snow_depth = "SHALLOW"
        elif material_id is MaterialID.SNOWONGRAVEL_MEDIUM:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "GRAVEL"
            self.snow_depth = "MEDIUM"
        elif material_id is MaterialID.SNOWONGRAVEL_DEEP:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "GRAVEL"
            self.snow_depth = "DEEP"
        elif material_id is MaterialID.SNOWONICE_SHALLOW:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "ICE"
            self.snow_depth = "SHALLOW"
        elif material_id is MaterialID.SNOWONICE_MEDIUM:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "ICE"
            self.snow_depth = "MEDIUM"
        elif material_id is MaterialID.SNOWONICE_DEEP:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "ICE"
            self.snow_depth = "DEEP"
        elif material_id is MaterialID.SNOWWALL_BOTTOM:
            self.category = "ROAD"
            self.road_surface = "SNOW"
            self.snow_subsurface = "BANK"

        elif material_id is MaterialID.COBBLE_DRY:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "COBBLE"
            self.wetness = "DRY"
        elif material_id is MaterialID.COBBLE_DAMP:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "COBBLE"
            self.wetness = "DAMP"
        elif material_id is MaterialID.COBBLE_WET:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "COBBLE"
            self.wetness = "WET"
        elif material_id is MaterialID.SETT_DRY:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "SETT"
            self.wetness = "DRY"
        elif material_id is MaterialID.SETT_DAMP:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "SETT"
            self.wetness = "DAMP"
        elif material_id is MaterialID.SETT_WET:
            self.category = "ROAD"
            self.road_surface = "COBBLE"
            self.cobble_type = "SETT"
            self.wetness = "WET"

        elif material_id is MaterialID.WATER_SURFACE:
            self.category = "GROUND"
            self.ground_surface = "WATER"

        elif material_id is MaterialID.GRASS_HARD_DRY:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "HARD"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRASS_HARD_DAMP:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "HARD"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRASS_HARD_WET:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "HARD"
            self.wetness = "WET"
        elif material_id is MaterialID.GRASS_MEDIUM_DRY:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "MEDIUM"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRASS_MEDIUM_DAMP:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "MEDIUM"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRASS_MEDIUM_WET:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "MEDIUM"
            self.wetness = "WET"
        elif material_id is MaterialID.GRASS_SOFT_DRY:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "SOFT"
            self.wetness = "DRY"
        elif material_id is MaterialID.GRASS_SOFT_DAMP:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "SOFT"
            self.wetness = "DAMP"
        elif material_id is MaterialID.GRASS_SOFT_WET:
            self.category = "GROUND"
            self.ground_surface = "GRASS"
            self.hardness = "SOFT"
            self.wetness = "WET"

        elif material_id is MaterialID.ROUGH_ROUGH_DRY:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "ROUGH"
            self.wetness = "DRY"
        elif material_id is MaterialID.ROUGH_ROUGH_WET:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "ROUGH"
            self.wetness = "WET"
        elif material_id is MaterialID.ROUGH_ROUGH_DAMP:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "ROUGH"
            self.wetness = "DAMP"
        elif material_id is MaterialID.ROUGH_VERYROUGH_DRY:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "VERYROUGH"
            self.wetness = "DRY"
        elif material_id is MaterialID.ROUGH_VERYROUGH_WET:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "VERYROUGH"
            self.wetness = "WET"
        elif material_id is MaterialID.ROUGH_VERYROUGH_DAMP:
            self.category = "GROUND"
            self.ground_surface = "ROUGH"
            self.rough_type = "VERYROUGH"
            self.wetness = "DAMP"

        elif material_id is MaterialID.DIRT_HARD_DRY:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "HARD"
            self.wetness = "DRY"
        elif material_id is MaterialID.DIRT_HARD_DAMP:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "HARD"
            self.wetness = "DAMP"
        elif material_id is MaterialID.DIRT_HARD_WET:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "HARD"
            self.wetness = "WET"
        elif material_id is MaterialID.DIRT_MEDIUM_DRY:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "MEDIUM"
            self.wetness = "DRY"
        elif material_id is MaterialID.DIRT_MEDIUM_DAMP:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "MEDIUM"
            self.wetness = "DAMP"
        elif material_id is MaterialID.DIRT_MEDIUM_WET:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "MEDIUM"
            self.wetness = "WET"
        elif material_id is MaterialID.DIRT_SOFT_DRY:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "SOFT"
            self.wetness = "DRY"
        elif material_id is MaterialID.DIRT_SOFT_DAMP:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "SOFT"
            self.wetness = "DAMP"
        elif material_id is MaterialID.DIRT_SOFT_WET:
            self.category = "GROUND"
            self.ground_surface = "DIRT"
            self.hardness = "SOFT"
            self.wetness = "WET"

        elif material_id is MaterialID.PASSTHROUGH:
            self.category = "PASSTHROUGH"

        else:
            return False
        return True

    def to_material_id(self) -> MaterialID:
        if self.category == "ROAD":
            if self.road_surface == "TARMAC":
                if self.tarmac_type == "FINE":
                    if self.tarmac_cleanliness == "CLEAN":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_FINE_CLEAN_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_FINE_CLEAN_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_FINE_CLEAN_WET
                    elif self.tarmac_cleanliness == "SPRINKLED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_FINE_SPRINKLED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_FINE_SPRINKLED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_FINE_SPRINKLED_WET
                    elif self.tarmac_cleanliness == "COVERED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_FINE_COVERED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_FINE_COVERED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_FINE_COVERED_WET
                elif self.tarmac_type == "MEDIUM":
                    if self.tarmac_cleanliness == "CLEAN":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_MEDIUM_CLEAN_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_MEDIUM_CLEAN_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_MEDIUM_CLEAN_WET
                    elif self.tarmac_cleanliness == "SPRINKLED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_MEDIUM_SPRINKLED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_MEDIUM_SPRINKLED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_MEDIUM_SPRINKLED_WET
                    elif self.tarmac_cleanliness == "COVERED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_MEDIUM_COVERED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_MEDIUM_COVERED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_MEDIUM_COVERED_WET
                elif self.tarmac_type == "COARSE":
                    if self.tarmac_cleanliness == "CLEAN":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_COARSE_CLEAN_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_COARSE_CLEAN_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_COARSE_CLEAN_WET
                    elif self.tarmac_cleanliness == "SPRINKLED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_COARSE_SPRINKLED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_COARSE_SPRINKLED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_COARSE_SPRINKLED_WET
                    elif self.tarmac_cleanliness == "COVERED":
                        if self.wetness == "DRY":
                            return MaterialID.TARMAC_COARSE_COVERED_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.TARMAC_COARSE_COVERED_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.TARMAC_COARSE_COVERED_WET
                elif self.tarmac_type == "BLACK_ICE":
                    return MaterialID.BLACK_ICE

            elif self.road_surface == "GRAVEL":
                if self.gravel_type == "US":
                    if self.gravel_depth == "SHALLOW":
                        if self.wetness == "DRY":
                            return MaterialID.US_GRAVEL_FINE_SHALLOW_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.US_GRAVEL_FINE_SHALLOW_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.US_GRAVEL_FINE_SHALLOW_WET
                    elif self.gravel_depth == "DEEP":
                        if self.wetness == "DRY":
                            return MaterialID.US_GRAVEL_FINE_DEEP_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.US_GRAVEL_FINE_DEEP_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.US_GRAVEL_FINE_DEEP_WET
                    elif self.gravel_depth == "DEEPER":
                        if self.wetness == "DRY":
                            return MaterialID.US_GRAVEL_FINE_DEEPER_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.US_GRAVEL_FINE_DEEPER_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.US_GRAVEL_FINE_DEEPER_WET
                elif self.gravel_type == "FINE":
                    if self.gravel_depth == "SHALLOW":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_FINE_SHALLOW_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_FINE_SHALLOW_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_FINE_SHALLOW_WET
                    elif self.gravel_depth == "DEEP":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_FINE_DEEP_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_FINE_DEEP_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_FINE_DEEP_WET
                    elif self.gravel_depth == "DEEPER":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_FINE_DEEPER_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_FINE_DEEPER_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_FINE_DEEPER_WET
                elif self.gravel_type == "MEDIUM":
                    if self.gravel_depth == "SHALLOW":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_MEDIUM_SHALLOW_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_MEDIUM_SHALLOW_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_MEDIUM_SHALLOW_WET
                    elif self.gravel_depth == "DEEP":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_MEDIUM_DEEP_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_MEDIUM_DEEP_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_MEDIUM_DEEP_WET
                    elif self.gravel_depth == "DEEPER":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_MEDIUM_DEEPER_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_MEDIUM_DEEPER_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_MEDIUM_DEEPER_WET
                elif self.gravel_type == "COARSE":
                    if self.gravel_depth == "SHALLOW":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_COARSE_SHALLOW_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_COARSE_SHALLOW_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_COARSE_SHALLOW_WET
                    elif self.gravel_depth == "DEEP":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_COARSE_DEEP_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_COARSE_DEEP_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_COARSE_DEEP_WET
                    elif self.gravel_depth == "DEEPER":
                        if self.wetness == "DRY":
                            return MaterialID.GRAVEL_COARSE_DEEPER_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.GRAVEL_COARSE_DEEPER_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.GRAVEL_COARSE_DEEPER_WET
                elif self.gravel_type == "BR":
                    if self.gravel_depth == "SHALLOW":
                        if self.wetness == "DRY":
                            return MaterialID.BR_GRAVEL_COARSE_SHALLOW_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.BR_GRAVEL_COARSE_SHALLOW_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.BR_GRAVEL_COARSE_SHALLOW_WET
                    elif self.gravel_depth == "DEEP":
                        if self.wetness == "DRY":
                            return MaterialID.BR_GRAVEL_COARSE_DEEP_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.BR_GRAVEL_COARSE_DEEP_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.BR_GRAVEL_COARSE_DEEP_WET
                    elif self.gravel_depth == "DEEPER":
                        if self.wetness == "DRY":
                            return MaterialID.BR_GRAVEL_COARSE_DEEPER_DRY
                        elif self.wetness == "DAMP":
                            return MaterialID.BR_GRAVEL_COARSE_DEEPER_DAMP
                        elif self.wetness == "WET":
                            return MaterialID.BR_GRAVEL_COARSE_DEEPER_WET

            elif self.road_surface == "SNOW":
                if self.snow_subsurface == "GRAVEL":
                    if self.snow_depth == "SHALLOW":
                        return MaterialID.SNOWONGRAVEL_SHALLOW
                    elif self.snow_depth == "MEDIUM":
                        return MaterialID.SNOWONGRAVEL_MEDIUM
                    elif self.snow_depth == "DEEP":
                        return MaterialID.SNOWONGRAVEL_DEEP
                elif self.snow_subsurface == "ICE":
                    if self.snow_depth == "SHALLOW":
                        return MaterialID.SNOWONICE_SHALLOW
                    elif self.snow_depth == "MEDIUM":
                        return MaterialID.SNOWONICE_MEDIUM
                    elif self.snow_depth == "DEEP":
                        return MaterialID.SNOWONICE_DEEP
                elif self.snow_subsurface == "BANK":
                    return MaterialID.SNOWWALL_BOTTOM

            elif self.road_surface == "COBBLE":
                if self.cobble_type == "COBBLE":
                    if self.wetness == "DRY":
                        return MaterialID.COBBLE_DRY
                    elif self.wetness == "DAMP":
                        return MaterialID.COBBLE_DAMP
                    elif self.wetness == "WET":
                        return MaterialID.COBBLE_WET
                elif self.cobble_type == "SETT":
                    if self.wetness == "DRY":
                        return MaterialID.SETT_DRY
                    elif self.wetness == "DAMP":
                        return MaterialID.SETT_DAMP
                    elif self.wetness == "WET":
                        return MaterialID.SETT_WET

        elif self.category == "GROUND":
            if self.ground_surface == "WATER":
                return MaterialID.WATER_SURFACE
            elif self.ground_surface == "GRASS":
                if self.hardness == "HARD":
                    if self.wetness == "DRY":
                        return MaterialID.GRASS_HARD_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.GRASS_HARD_DAMP
                    if self.wetness == "WET":
                        return MaterialID.GRASS_HARD_WET
                elif self.hardness == "MEDIUM":
                    if self.wetness == "DRY":
                        return MaterialID.GRASS_MEDIUM_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.GRASS_MEDIUM_DAMP
                    if self.wetness == "WET":
                        return MaterialID.GRASS_MEDIUM_WET
                elif self.hardness == "SOFT":
                    if self.wetness == "DRY":
                        return MaterialID.GRASS_SOFT_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.GRASS_SOFT_DAMP
                    if self.wetness == "WET":
                        return MaterialID.GRASS_SOFT_WET
            elif self.ground_surface == "ROUGH":
                if self.rough_type == "ROUGH":
                    if self.wetness == "DRY":
                        return MaterialID.ROUGH_ROUGH_DRY
                    elif self.wetness == "WET":
                        return MaterialID.ROUGH_ROUGH_WET
                    elif self.wetness == "DAMP":
                        return MaterialID.ROUGH_ROUGH_DAMP
                elif self.rough_type == "VERYROUGH":
                    if self.wetness == "DRY":
                        return MaterialID.ROUGH_VERYROUGH_DRY
                    elif self.wetness == "WET":
                        return MaterialID.ROUGH_VERYROUGH_WET
                    elif self.wetness == "DAMP":
                        return MaterialID.ROUGH_VERYROUGH_DAMP
            elif self.ground_surface == "DIRT":
                if self.hardness == "HARD":
                    if self.wetness == "DRY":
                        return MaterialID.DIRT_HARD_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.DIRT_HARD_DAMP
                    if self.wetness == "WET":
                        return MaterialID.DIRT_HARD_WET
                elif self.hardness == "MEDIUM":
                    if self.wetness == "DRY":
                        return MaterialID.DIRT_MEDIUM_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.DIRT_MEDIUM_DAMP
                    if self.wetness == "WET":
                        return MaterialID.DIRT_MEDIUM_WET
                elif self.hardness == "SOFT":
                    if self.wetness == "DRY":
                        return MaterialID.DIRT_SOFT_DRY
                    if self.wetness == "DAMP":
                        return MaterialID.DIRT_SOFT_DAMP
                    if self.wetness == "WET":
                        return MaterialID.DIRT_SOFT_WET

        elif self.category == "PASSTHROUGH":
            return MaterialID.PASSTHROUGH

        raise NotImplementedError


def register() -> None:
    bpy.utils.register_class(RBRMaterialPicker)
    bpy.types.Scene.rbr_material_picker = bpy.props.PointerProperty(
        type=RBRMaterialPicker,
    )


def unregister() -> None:
    bpy.utils.unregister_class(RBRMaterialPicker)
    del bpy.types.Scene.rbr_material_picker


@dataclass
class RGB:
    r: int
    g: int
    b: int


def material_id_to_color(m: MaterialID) -> RGB:
    if m is MaterialID.UNDEFINED:
        return RGB(255, 255, 255)
    if m is MaterialID.GRAVEL_FINE_DEEPER_DRY:
        return RGB(255, 85, 0)
    if m is MaterialID.GRAVEL_FINE_DEEPER_DAMP:
        return RGB(221, 51, 0)
    if m is MaterialID.GRAVEL_FINE_DEEPER_WET:
        return RGB(195, 25, 0)
    if m is MaterialID.GRAVEL_MEDIUM_DEEPER_DRY:
        return RGB(255, 0, 0)
    if m is MaterialID.GRAVEL_MEDIUM_DEEPER_DAMP:
        return RGB(205, 0, 0)
    if m is MaterialID.GRAVEL_MEDIUM_DEEPER_WET:
        return RGB(151, 0, 0)
    if m is MaterialID.GRAVEL_FINE_DEEP_DRY:
        return RGB(218, 97, 37)
    if m is MaterialID.GRAVEL_FINE_DEEP_DAMP:
        return RGB(189, 68, 32)
    if m is MaterialID.GRAVEL_FINE_DEEP_WET:
        return RGB(167, 46, 28)
    if m is MaterialID.GRAVEL_MEDIUM_DEEP_DRY:
        return RGB(218, 37, 37)
    if m is MaterialID.GRAVEL_MEDIUM_DEEP_DAMP:
        return RGB(175, 29, 29)
    if m is MaterialID.GRAVEL_MEDIUM_DEEP_WET:
        return RGB(129, 22, 22)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_DRY:
        return RGB(190, 106, 64)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_DAMP:
        return RGB(165, 81, 56)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_WET:
        return RGB(145, 61, 49)
    if m is MaterialID.GRAVEL_MEDIUM_SHALLOW_DRY:
        return RGB(190, 64, 64)
    if m is MaterialID.GRAVEL_MEDIUM_SHALLOW_DAMP:
        return RGB(153, 52, 52)
    if m is MaterialID.GRAVEL_MEDIUM_SHALLOW_WET:
        return RGB(112, 38, 38)
    if m is MaterialID.SPRET_BUSH_SMALL:
        return RGB(255, 255, 255)
    if m is MaterialID.SPRET_BUSH_MEDIUM:
        return RGB(255, 255, 255)
    if m is MaterialID.SPRET_BUSH_LARGE:
        return RGB(255, 255, 255)
    if m is MaterialID.LOV_BUSH_SMALL:
        return RGB(255, 255, 255)
    if m is MaterialID.LOV_BUSH_MEDIUM:
        return RGB(255, 255, 255)
    if m is MaterialID.LOV_BUSH_LARGE:
        return RGB(255, 255, 255)
    if m is MaterialID.TREE_SMALL:
        return RGB(255, 255, 255)
    if m is MaterialID.TREE_MEDIUM:
        return RGB(255, 255, 255)
    if m is MaterialID.TREE_LARGE:
        return RGB(255, 255, 255)
    if m is MaterialID.GRAVEL_COARSE_DEEPER_DRY:
        return RGB(255, 0, 85)
    if m is MaterialID.GRAVEL_COARSE_DEEPER_DAMP:
        return RGB(200, 0, 30)
    if m is MaterialID.GRAVEL_COARSE_DEEPER_WET:
        return RGB(183, 24, 24)
    if m is MaterialID.TARMAC_FINE_CLEAN_DRY:
        return RGB(0, 211, 255)
    if m is MaterialID.TARMAC_FINE_CLEAN_DAMP:
        return RGB(0, 180, 224)
    if m is MaterialID.TARMAC_FINE_CLEAN_WET:
        return RGB(0, 136, 180)
    if m is MaterialID.GRAVEL_COARSE_DEEP_DRY:
        return RGB(218, 37, 97)
    if m is MaterialID.GRAVEL_COARSE_DEEP_DAMP:
        return RGB(171, 29, 50)
    if m is MaterialID.GRAVEL_COARSE_DEEP_WET:
        return RGB(143, 24, 24)
    if m is MaterialID.TARMAC_FINE_SPRINKLED_DRY:
        return RGB(52, 176, 203)
    if m is MaterialID.TARMAC_FINE_SPRINKLED_DAMP:
        return RGB(45, 152, 178)
    if m is MaterialID.TARMAC_FINE_SPRINKLED_WET:
        return RGB(36, 117, 143)
    if m is MaterialID.GRAVEL_COARSE_SHALLOW_DRY:
        return RGB(190, 64, 106)
    if m is MaterialID.GRAVEL_COARSE_SHALLOW_DAMP:
        return RGB(149, 51, 66)
    if m is MaterialID.GRAVEL_COARSE_SHALLOW_WET:
        return RGB(124, 42, 42)
    if m is MaterialID.TARMAC_FINE_COVERED_DRY:
        return RGB(77, 159, 177)
    if m is MaterialID.TARMAC_FINE_COVERED_DAMP:
        return RGB(68, 138, 155)
    if m is MaterialID.TARMAC_FINE_COVERED_WET:
        return RGB(55, 108, 125)
    if m is MaterialID.ROCK_SMALL:
        return RGB(255, 255, 255)
    if m is MaterialID.ROCK_MEDIUM:
        return RGB(255, 255, 255)
    if m is MaterialID.ROCK_LARGE:
        return RGB(255, 255, 255)
    if m is MaterialID.TRUNK_SMALL:
        return RGB(255, 255, 255)
    if m is MaterialID.TRUNK_MEDIUM:
        return RGB(255, 255, 255)
    if m is MaterialID.TRUNK_LARGE:
        return RGB(255, 255, 255)
    if m is MaterialID.SNOWWALL:
        return RGB(255, 255, 255)
    if m is MaterialID.METAL_POLE:
        return RGB(255, 255, 255)
    if m is MaterialID.METAL_BARRIER:
        return RGB(255, 255, 255)
    if m is MaterialID.TARMAC_MEDIUM_CLEAN_DRY:
        return RGB(0, 0, 255)
    if m is MaterialID.TARMAC_MEDIUM_CLEAN_DAMP:
        return RGB(0, 0, 206)
    if m is MaterialID.TARMAC_MEDIUM_CLEAN_WET:
        return RGB(0, 0, 155)
    if m is MaterialID.TARMAC_COARSE_CLEAN_DRY:
        return RGB(182, 0, 255)
    if m is MaterialID.TARMAC_COARSE_CLEAN_DAMP:
        return RGB(141, 0, 200)
    if m is MaterialID.TARMAC_COARSE_CLEAN_WET:
        return RGB(92, 0, 136)
    if m is MaterialID.TARMAC_MEDIUM_SPRINKLED_DRY:
        return RGB(52, 52, 203)
    if m is MaterialID.TARMAC_MEDIUM_SPRINKLED_DAMP:
        return RGB(42, 42, 164)
    if m is MaterialID.TARMAC_MEDIUM_SPRINKLED_WET:
        return RGB(31, 31, 123)
    if m is MaterialID.TARMAC_COARSE_SPRINKLED_DRY:
        return RGB(160, 52, 203)
    if m is MaterialID.TARMAC_COARSE_SPRINKLED_DAMP:
        return RGB(123, 36, 158)
    if m is MaterialID.TARMAC_COARSE_SPRINKLED_WET:
        return RGB(78, 12, 104)
    if m is MaterialID.TARMAC_MEDIUM_COVERED_DRY:
        return RGB(77, 77, 177)
    if m is MaterialID.TARMAC_MEDIUM_COVERED_DAMP:
        return RGB(63, 63, 143)
    if m is MaterialID.TARMAC_MEDIUM_COVERED_WET:
        return RGB(47, 47, 108)
    if m is MaterialID.TARMAC_COARSE_COVERED_DRY:
        return RGB(129, 84, 148)
    if m is MaterialID.TARMAC_COARSE_COVERED_DAMP:
        return RGB(98, 62, 113)
    if m is MaterialID.TARMAC_COARSE_COVERED_WET:
        return RGB(59, 31, 70)
    if m is MaterialID.COBBLE_DRY:
        return RGB(180, 40, 220)
    if m is MaterialID.COBBLE_DAMP:
        return RGB(160, 20, 200)
    if m is MaterialID.COBBLE_WET:
        return RGB(140, 0, 180)
    if m is MaterialID.SETT_DRY:
        return RGB(180, 220, 40)
    if m is MaterialID.SETT_DAMP:
        return RGB(160, 200, 20)
    if m is MaterialID.SETT_WET:
        return RGB(140, 180, 0)
    if m is MaterialID.SNOWWALL_BOTTOM:
        return RGB(255, 255, 255)
    if m is MaterialID.GRASS_HARD_DRY:
        return RGB(0, 255, 76)
    if m is MaterialID.GRASS_HARD_DAMP:
        return RGB(0, 217, 90)
    if m is MaterialID.GRASS_HARD_WET:
        return RGB(0, 165, 68)
    if m is MaterialID.SNOWONGRAVEL_SHALLOW:
        return RGB(255, 252, 0)
    if m is MaterialID.SNOWONGRAVEL_MEDIUM:
        return RGB(203, 201, 52)
    if m is MaterialID.SNOWONGRAVEL_DEEP:
        return RGB(163, 162, 91)
    if m is MaterialID.GRASS_MEDIUM_DRY:
        return RGB(47, 208, 95)
    if m is MaterialID.GRASS_MEDIUM_DAMP:
        return RGB(40, 177, 97)
    if m is MaterialID.GRASS_MEDIUM_WET:
        return RGB(30, 134, 73)
    if m is MaterialID.GRASS_SOFT_DRY:
        return RGB(87, 167, 111)
    if m is MaterialID.GRASS_SOFT_DAMP:
        return RGB(74, 142, 102)
    if m is MaterialID.GRASS_SOFT_WET:
        return RGB(56, 108, 78)
    if m is MaterialID.BLACK_ICE:
        return RGB(159, 159, 159)
    if m is MaterialID.SNOWONICE_SHALLOW:
        return RGB(159, 255, 0)
    if m is MaterialID.SNOWONICE_MEDIUM:
        return RGB(147, 208, 47)
    if m is MaterialID.SNOWONICE_DEEP:
        return RGB(138, 174, 79)
    if m is MaterialID.TREE_STUMP:
        return RGB(255, 255, 255)
    if m is MaterialID.BENDABLE_TREE:
        return RGB(255, 255, 255)
    if m is MaterialID.ROUGH_ROUGH_DRY:
        return RGB(255, 0, 255)
    if m is MaterialID.ROUGH_ROUGH_WET:
        return RGB(168, 0, 168)
    if m is MaterialID.ROUGH_ROUGH_DAMP:
        return RGB(200, 0, 200)
    if m is MaterialID.DIRT_HARD_DRY:
        return RGB(255, 168, 0)
    if m is MaterialID.DIRT_HARD_DAMP:
        return RGB(209, 122, 0)
    if m is MaterialID.DIRT_HARD_WET:
        return RGB(158, 71, 0)
    if m is MaterialID.ROUGH_VERYROUGH_DRY:
        return RGB(199, 56, 198)
    if m is MaterialID.ROUGH_VERYROUGH_WET:
        return RGB(131, 37, 131)
    if m is MaterialID.ROUGH_VERYROUGH_DAMP:
        return RGB(170, 45, 160)
    if m is MaterialID.DIRT_MEDIUM_DRY:
        return RGB(183, 145, 72)
    if m is MaterialID.DIRT_MEDIUM_DAMP:
        return RGB(150, 112, 59)
    if m is MaterialID.DIRT_MEDIUM_WET:
        return RGB(113, 75, 44)
    if m is MaterialID.DIRT_SOFT_DRY:
        return RGB(155, 136, 100)
    if m is MaterialID.DIRT_SOFT_DAMP:
        return RGB(127, 108, 82)
    if m is MaterialID.DIRT_SOFT_WET:
        return RGB(95, 76, 61)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_DRY_CLONE:
        return RGB(215, 215, 175)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_DAMP_CLONE:
        return RGB(183, 183, 149)
    if m is MaterialID.GRAVEL_FINE_SHALLOW_WET_CLONE:
        return RGB(145, 145, 118)
    if m is MaterialID.WATER_SURFACE:
        return RGB(0, 0, 175)
    if m is MaterialID.DIRT_HARD_DRY_CLONE:
        return RGB(186, 186, 123)
    if m is MaterialID.DIRT_HARD_DAMP_CLONE:
        return RGB(159, 159, 104)
    if m is MaterialID.DIRT_HARD_WET_CLONE:
        return RGB(126, 126, 81)
    if m is MaterialID.VERY_SPARSE_BUSH:
        return RGB(220, 220, 220)
    if m is MaterialID.SPARSE_BUSH:
        return RGB(175, 175, 175)
    if m is MaterialID.DENSE_BUSH:
        return RGB(100, 100, 100)
    if m is MaterialID.VERY_DENSE_BUSH:
        return RGB(255, 255, 255)
    if m is MaterialID.US_GRAVEL_FINE_SHALLOW_DRY:
        return RGB(190, 106, 64)
    if m is MaterialID.US_GRAVEL_FINE_SHALLOW_DAMP:
        return RGB(165, 81, 56)
    if m is MaterialID.US_GRAVEL_FINE_SHALLOW_WET:
        return RGB(145, 61, 49)
    if m is MaterialID.BR_GRAVEL_COARSE_SHALLOW_DRY:
        return RGB(190, 146, 64)
    if m is MaterialID.BR_GRAVEL_COARSE_SHALLOW_DAMP:
        return RGB(165, 121, 56)
    if m is MaterialID.BR_GRAVEL_COARSE_SHALLOW_WET:
        return RGB(145, 101, 49)
    if m is MaterialID.US_GRAVEL_FINE_DEEP_DRY:
        return RGB(210, 106, 64)
    if m is MaterialID.US_GRAVEL_FINE_DEEP_DAMP:
        return RGB(185, 81, 56)
    if m is MaterialID.US_GRAVEL_FINE_DEEP_WET:
        return RGB(165, 61, 49)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEP_DRY:
        return RGB(210, 146, 64)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEP_DAMP:
        return RGB(185, 121, 56)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEP_WET:
        return RGB(165, 101, 49)
    if m is MaterialID.US_GRAVEL_FINE_DEEPER_DRY:
        return RGB(230, 146, 64)
    if m is MaterialID.US_GRAVEL_FINE_DEEPER_DAMP:
        return RGB(205, 121, 56)
    if m is MaterialID.US_GRAVEL_FINE_DEEPER_WET:
        return RGB(185, 101, 49)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEPER_DRY:
        return RGB(230, 146, 64)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEPER_DAMP:
        return RGB(205, 121, 56)
    if m is MaterialID.BR_GRAVEL_COARSE_DEEPER_WET:
        return RGB(185, 101, 49)
    if m is MaterialID.PASSTHROUGH:
        return RGB(100, 100, 100)
    if m is MaterialID.SPECTATOR:
        return RGB(0, 0, 255)
    return RGB(255, 255, 255)
