import bpy  # type: ignore

from typing import List, Optional, Set, Tuple

from rbr_track_formats.mat import SurfaceType, SurfaceAge
from rbr_track_formats.track_settings import (
    CloudName,
    TintSet,
    TimeOfDay,
    Weather,
    Sky,
)

from .blender_ops import copy_linked_scene
from .physical_material_editor.operator import RBR_OT_edit_material_maps
from .shaders import sky
from .shaders.sky import update_sky_value, update_sky_vector, update_sun_dir
from .shaders.texture import all_rbr_texture_nodes


def migrate_world_weathers() -> None:
    init_scene = bpy.context.scene
    settings = init_scene.rbr_track_settings
    open_tint_set = settings.get_tint_set()

    def make_world(
        tint_set: TintSet, time_of_day: TimeOfDay, weathers: RBRWeathersDEPRECATED
    ) -> None:
        if len(weathers.weathers) == 0:
            return

        scene = bpy.data.scenes.get(tint_set.name)
        if scene is None:
            scene = copy_linked_scene(init_scene)
            scene.name = tint_set.name
            scene.rbr_track_settings.tint_set = tint_set.name
        if open_tint_set == tint_set:
            bpy.context.window.scene = scene

        for weather in weathers.weathers:
            world = bpy.data.worlds.new(f"{tint_set} {weather.weather} {weather.sky}")
            new_weather = world.rbr_track_settings
            new_weather.weather = weather.weather
            new_weather.sky = weather.sky
            new_weather.cloud_name = weather.cloud_name
            new_weather.extinction = weather.extinction
            new_weather.terrain_reflectance_multiplier = (
                weather.terrain_reflectance_multiplier
            )
            new_weather.specular_glossiness = weather.specular_glossiness
            new_weather.specular_alpha = weather.specular_alpha
            new_weather.use_fog = weather.use_fog
            new_weather.fog_start = weather.fog_start
            new_weather.fog_end = weather.fog_end
            new_weather.superbowl_fog_start = weather.superbowl_fog_start
            new_weather.superbowl_fog_end = weather.superbowl_fog_end
            new_weather.greenstein_value = weather.greenstein_value
            new_weather.inscattering = weather.inscattering
            new_weather.mie_multiplier = weather.mie_multiplier
            new_weather.rayleigh_multiplier = weather.rayleigh_multiplier
            new_weather.skybox_saturation = weather.skybox_saturation
            new_weather.skybox_scale = weather.skybox_scale
            new_weather.superbowl_scale = weather.superbowl_scale
            new_weather.sun_intensity = weather.sun_intensity
            new_weather.sun_offset = weather.sun_offset
            new_weather.turbidity = weather.turbidity
            new_weather.car_ambient_lighting = weather.car_ambient_lighting
            new_weather.car_diffuse_lighting = weather.car_diffuse_lighting
            new_weather.car_deep_shadow_alpha = weather.car_deep_shadow_alpha
            new_weather.car_shadow_alpha = weather.car_shadow_alpha
            new_weather.character_lighting = weather.character_lighting
            new_weather.cloud_scale = weather.cloud_scale
            new_weather.mipmapbias = weather.mipmapbias
            new_weather.particle_lighting = weather.particle_lighting

            new_weather.terrain_reflectance_color = (
                weather.terrain_reflectance_color.copy()
            )
            new_weather.fog_color = weather.fog_color.copy()
            new_weather.ambient = weather.ambient.copy()

            ptr = scene.rbr_track_settings.world_weathers.add()
            ptr.world = world
            ptr.overcast_time_of_day = time_of_day.name

    make_world(TintSet.MORNING, TimeOfDay.MORNING, settings.morning_weathers)
    make_world(TintSet.NOON, TimeOfDay.NOON, settings.noon_weathers)
    make_world(TintSet.EVENING, TimeOfDay.EVENING, settings.evening_weathers)
    make_world(TintSet.OVERCAST, TimeOfDay.MORNING, settings.overcast_morning_weathers)
    make_world(TintSet.OVERCAST, TimeOfDay.NOON, settings.overcast_noon_weathers)
    make_world(TintSet.OVERCAST, TimeOfDay.EVENING, settings.overcast_evening_weathers)


class RBR_OT_add_world_weather_sky(bpy.types.Operator):
    bl_idname = "rbr.add_world_weather_sky"
    bl_label = "Add Weather"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        next_index = len(context.scene.rbr_track_settings.world_weathers)
        context.scene.rbr_track_settings.world_weathers.add()
        context.scene.rbr_track_settings.active_world_weather = next_index
        context.scene.rbr_track_settings.update_world_context(context)
        return {"FINISHED"}


class RBR_OT_remove_world_weather_sky(bpy.types.Operator):
    bl_idname = "rbr.remove_world_weather_sky"
    bl_label = "Remove Weather"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(default=0)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        context.scene.rbr_track_settings.world_weathers.remove(self.index)
        context.scene.rbr_track_settings.update_world_context(context)
        return {"FINISHED"}


class RBRWorldWeatherPtr(bpy.types.PropertyGroup):
    def update_world(self, context: bpy.types.Context) -> None:
        context.scene.rbr_track_settings.update_world_context(context)
        context.scene.rbr_track_settings.update_sky_values()

    world: bpy.props.PointerProperty(  # type: ignore
        type=bpy.types.World,
        update=lambda self, context: self.update_world(context),
    )
    overcast_time_of_day: bpy.props.EnumProperty(  # type: ignore
        name="Overcast",  # noqa: F821
        description="Overcast Time of Day",
        items=[(t.name, t.pretty(), t.pretty()) for t in TimeOfDay],
        default=TimeOfDay.MORNING.name,
    )


class RBRWeatherSky(bpy.types.PropertyGroup):
    weather: bpy.props.EnumProperty(  # type: ignore
        name="Weather",
        default=Weather.CRISP.name,
        items=[(w.name, w.pretty(), w.pretty(), w.id()) for w in Weather],
    )
    sky: bpy.props.EnumProperty(  # type: ignore
        name="Sky",
        default=Sky.CLEAR.name,
        items=[(s.name, s.pretty(), s.pretty(), s.id()) for s in Sky],
    )
    cloud_name: bpy.props.EnumProperty(  # type: ignore
        name="Cloud Name",
        default=CloudName.CLEAR.name,
        items=[(s.name, s.pretty(), s.pretty(), s.id()) for s in CloudName],
    )
    extinction: bpy.props.FloatProperty(  # type: ignore
        name="Extinction",  # noqa: F821
        default=0.45,
        min=0.0,
        max=1.0,
        step=1,
        update=lambda self, _: update_sky_value(sky.SKY_EXTINCTION, self.extinction),
    )
    terrain_reflectance_color: bpy.props.FloatVectorProperty(  # type: ignore
        name="Terrain Reflectance Color",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype="COLOR",  # noqa: F821
        update=lambda self, _: update_sky_vector(
            sky.SKY_TERRAIN_REFLECTANCE_COLOR, self.terrain_reflectance_color
        ),
    )
    terrain_reflectance_multiplier: bpy.props.FloatProperty(  # type: ignore
        name="Terrain Reflectance Multiplier",
        default=0.2,
        min=0.0,
        max=0.2,
        update=lambda self, _: update_sky_value(
            sky.SKY_TERRAIN_REFLECTANCE_MULTIPLIER, self.terrain_reflectance_multiplier
        ),
    )
    specular_glossiness: bpy.props.FloatProperty(  # type: ignore
        name="Specular Glossiness",
        default=4.0,
        min=1.0,
        max=14.0,
        update=lambda self, _: update_sky_value(
            sky.SKY_SPECULAR_GLOSSINESS, self.specular_glossiness
        ),
    )
    specular_alpha: bpy.props.FloatProperty(  # type: ignore
        name="Specular Alpha",
        default=0.42,
        min=0.11,
        max=1.0,
        update=lambda self, _: update_sky_value(
            sky.SKY_SPECULAR_ALPHA, self.specular_alpha
        ),
    )
    use_fog: bpy.props.BoolProperty(  # type: ignore
        name="Use Fog",
        default=False,
        update=lambda self, _: update_sky_value(sky.SKY_USE_FOG, self.use_fog),
    )
    fog_color: bpy.props.FloatVectorProperty(  # type: ignore
        name="Fog Color",
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
        subtype="COLOR",  # noqa: F821
        update=lambda self, _: update_sky_vector(sky.SKY_FOG_COLOR, self.fog_color),
    )
    fog_start: bpy.props.FloatProperty(  # type: ignore
        name="Fog Start",
        default=0.0,
        min=-3000.0,
        max=1000.0,
        update=lambda self, _: update_sky_value(sky.SKY_FOG_START, self.fog_start),
    )
    fog_end: bpy.props.FloatProperty(  # type: ignore
        name="Fog End",
        default=1000.0,
        min=-1000.0,
        max=3000.0,
        update=lambda self, _: update_sky_value(sky.SKY_FOG_END, self.fog_end),
    )
    superbowl_fog_start: bpy.props.FloatProperty(  # type: ignore
        name="Superbowl Fog Start",
        default=0.0,
        min=-10000.0,
        max=1000.0,
        update=lambda self, _: update_sky_value(
            sky.SKY_SUPERBOWL_FOG_START, self.superbowl_fog_start
        ),
    )
    superbowl_fog_end: bpy.props.FloatProperty(  # type: ignore
        name="Superbowl Fog End",
        default=1000.0,
        min=-1000.0,
        max=10000.0,
        update=lambda self, _: update_sky_value(
            sky.SKY_SUPERBOWL_FOG_END, self.superbowl_fog_end
        ),
    )
    greenstein_value: bpy.props.FloatProperty(  # type: ignore
        name="Greenstein Value",
        default=1.0,
        min=-1.0,
        max=1.0,
        step=1,
        update=lambda self, _: update_sky_value(
            sky.SKY_GREENSTEIN_VALUE, self.greenstein_value
        ),
    )
    inscattering: bpy.props.FloatProperty(  # type: ignore
        name="Inscattering",  # noqa: F821
        default=0.33,
        min=0.0,
        max=1.0,
        step=1,
        update=lambda self, _: update_sky_value(
            sky.SKY_INSCATTERING, self.inscattering
        ),
    )
    mie_multiplier: bpy.props.FloatProperty(  # type: ignore
        name="Mie Multiplier",
        default=0.001,
        min=0.0,
        max=0.1,
        precision=6,
        step=1,
        update=lambda self, _: update_sky_value(
            sky.SKY_MIE_MULTIPLIER, self.mie_multiplier
        ),
    )
    rayleigh_multiplier: bpy.props.FloatProperty(  # type: ignore
        name="Rayleigh Multiplier",
        default=0.04096,
        min=0.0,
        max=1.0,
        precision=6,
        step=1,
        update=lambda self, _: update_sky_value(
            sky.SKY_RAYLEIGH_MULTIPLIER, self.rayleigh_multiplier
        ),
    )
    skybox_saturation: bpy.props.FloatProperty(  # type: ignore
        name="Skybox Saturation",
        default=1.0,
        min=0.0,
        max=1.0,
        step=10,
        update=lambda self, _: update_sky_value(
            sky.SKY_SKYBOX_SATURATION, self.skybox_saturation
        ),
    )
    skybox_scale: bpy.props.FloatProperty(  # type: ignore
        name="Skybox Scale",
        default=97.0,
        min=1.0,
        max=100.0,
        step=10,
        update=lambda self, _: update_sky_value(
            sky.SKY_SKYBOX_SCALE, self.skybox_scale
        ),
    )
    superbowl_scale: bpy.props.FloatProperty(  # type: ignore
        name="Superbowl Scale",
        default=0.15,
        min=0.0,
        max=2.0,
        update=lambda self, _: update_sky_value(
            sky.SKY_SUPERBOWL_SCALE, self.superbowl_scale
        ),
    )
    sun_intensity: bpy.props.FloatProperty(  # type: ignore
        name="Sun Intensity",
        default=98.0,
        min=30.0,
        max=200.0,
        step=10,
        update=lambda self, _: update_sky_value(
            sky.SKY_SUN_INTENSITY, self.sun_intensity
        ),
    )
    sun_offset: bpy.props.FloatProperty(  # type: ignore
        name="Sun Offset",
        default=-0.02,
        min=-3.0,
        max=3.0,
        step=1,
        update=lambda self, _: update_sky_value(sky.SKY_SUN_OFFSET, self.sun_offset),
    )
    turbidity: bpy.props.FloatProperty(  # type: ignore
        name="Turbidity",  # noqa: F821
        default=0.0,
        min=0.0,
        max=9.0,
        step=1,
        update=lambda self, _: update_sky_value(sky.SKY_TURBIDITY, self.turbidity),
    )

    # The following do not alter the sky shaders.
    ambient: bpy.props.FloatVectorProperty(  # type: ignore
        name="Ambient",  # noqa: F821
        default=(0.5, 0.5, 0.5),
        min=0.0,
        max=1.0,
        subtype="COLOR",  # noqa: F821
    )
    car_ambient_lighting: bpy.props.FloatProperty(  # type: ignore
        name="Car Ambient Lighting",  # noqa: F821
        default=1.74,
        min=0.2,
        max=4.0,
        step=1,
    )
    car_diffuse_lighting: bpy.props.FloatProperty(  # type: ignore
        name="Car Diffuse Lighting",  # noqa: F821
        default=1.9,
        min=0.5,
        max=2.0,
        step=1,
    )
    car_deep_shadow_alpha: bpy.props.FloatProperty(  # type: ignore
        name="Car Deep Shadow Alpha",  # noqa: F821
        default=1.0,
        min=0.0,
        max=0.5,
        step=1,
    )
    car_shadow_alpha: bpy.props.FloatProperty(  # type: ignore
        name="Car Shadow Alpha",  # noqa: F821
        default=0.24,
        min=0.0,
        max=1.5,
        step=1,
    )
    character_lighting: bpy.props.FloatProperty(  # type: ignore
        name="Character Lighting",  # noqa: F821
        default=1.0,
        min=1.0,
        max=2.0,
        step=1,
    )
    cloud_scale: bpy.props.FloatProperty(  # type: ignore
        name="Cloud Scale",  # noqa: F821
        default=10.0,
        min=0.0,
        max=250.0,
        step=1,
    )
    mipmapbias: bpy.props.FloatProperty(  # type: ignore
        name="Mipmap Bias",  # noqa: F821
        default=-3,
        min=-4,
        max=-2,
        step=1,
    )
    particle_lighting: bpy.props.FloatProperty(  # type: ignore
        name="Particle Lighting",  # noqa: F821
        default=1.0,
        min=0.5,
        max=2.0,
        step=1,
    )

    def draw(self, layout: bpy.types.UILayout) -> None:
        top = layout.row()
        top.prop(self, "weather")
        top.prop(self, "sky")
        layout.prop(self, "use_fog")
        if self.use_fog:
            layout.prop(self, "fog_color")
            layout.prop(self, "fog_start", slider=True)
            layout.prop(self, "fog_end", slider=True)
            layout.prop(self, "superbowl_fog_start", slider=True)
            layout.prop(self, "superbowl_fog_end", slider=True)
            layout.prop(self, "skybox_saturation", slider=True)
        layout.prop(self, "cloud_name")
        layout.prop(self, "extinction", slider=True)
        layout.prop(self, "greenstein_value", slider=True)
        layout.prop(self, "inscattering", slider=True)
        layout.prop(self, "mie_multiplier", slider=True)
        layout.prop(self, "rayleigh_multiplier", slider=True)
        layout.prop(self, "skybox_scale", slider=True)
        layout.prop(self, "specular_alpha", slider=True)
        layout.prop(self, "specular_glossiness", slider=True)
        layout.prop(self, "sun_intensity", slider=True)
        layout.prop(self, "sun_offset", slider=True)
        layout.prop(self, "superbowl_scale", slider=True)
        layout.prop(self, "terrain_reflectance_color")
        layout.prop(self, "terrain_reflectance_multiplier", slider=True)
        layout.prop(self, "turbidity", slider=True)

        layout.separator()
        layout.prop(self, "ambient")
        layout.prop(self, "car_ambient_lighting", slider=True)
        layout.prop(self, "car_diffuse_lighting", slider=True)
        layout.prop(self, "car_deep_shadow_alpha", slider=True)
        layout.prop(self, "car_shadow_alpha", slider=True)
        layout.prop(self, "character_lighting", slider=True)
        layout.prop(self, "cloud_scale", slider=True)
        layout.prop(self, "mipmapbias", slider=True)
        layout.prop(self, "particle_lighting", slider=True)


class RBRWeathersDEPRECATED(bpy.types.PropertyGroup):
    """DEPRECATED but kept for migrations"""

    weathers: bpy.props.CollectionProperty(  # type: ignore
        type=RBRWeatherSky,
    )


def setup_rbr_world(world: bpy.types.World) -> None:
    """Function to connect an RBR sky node to an eevee world output. Tries not
    to break the user output (unless they happen to have connected something
    else to the eevee output)."""
    world.use_nodes = True
    node_tree = world.node_tree
    world_output = None
    # Find the first eevee output node
    for node in node_tree.nodes:
        if node.type == "OUTPUT_WORLD" and node.target == "EEVEE":
            world_output = node
            break
    # Change any "All" outputs to just output to cycles - that way they can't
    # interfere with the RBR sky.
    for node in node_tree.nodes:
        if node.type == "OUTPUT_WORLD" and node.target == "ALL":
            node.target = "CYCLES"
    # Or create one if missing
    if world_output is None:
        world_output = node_tree.nodes.new("ShaderNodeOutputWorld")
        world_output.target = "EEVEE"
    # Find a sky node
    sky_node = None
    for node in node_tree.nodes:
        if isinstance(node, sky.ShaderNodeRBRSky):
            sky_node = node
    # Or create one if missing
    if sky_node is None:
        sky_node = node_tree.nodes.new("ShaderNodeRBRSky")
    node_tree.links.new(world_output.inputs["Surface"], sky_node.outputs["Surface"])


class RBRTrackSettings(bpy.types.PropertyGroup):
    def __update_surface_type__(self, context: bpy.types.Context) -> None:
        # Prevent users from disabling all surface types.
        if len(self.surface_types) < 1:
            self.surface_types = {SurfaceType.DRY.name}
        # Detect if we've disabled the currently active surface and reset it
        # This prints a warning when true, unfortunately
        if self.active_surface_type == "":
            self.active_surface_type = self.selected_surface_types()[0].name

    # This property has an invariant: at least one option must be selected.
    surface_types: bpy.props.EnumProperty(  # type: ignore
        name="Surface Types",
        description="Surface types for this track",
        items=[(t.name, t.pretty(), t.pretty(), t.bitmask()) for t in SurfaceType],
        default={SurfaceType.DRY.name},
        options={"ENUM_FLAG"},  # noqa: F821
        update=__update_surface_type__,
    )

    def selected_surface_types(self) -> List[SurfaceType]:
        """Return the possible surface types for this stage"""
        return [SurfaceType[s] for s in self.surface_types]

    # Update anything which depends on these values
    def __update_conditions__(self, context: bpy.types.Context) -> None:
        # TODO do this for each _tree_, not each _node_.
        for node in all_rbr_texture_nodes():
            node.link_context_active_texture(context)
        if RBR_OT_edit_material_maps.active_operator is not None:
            RBR_OT_edit_material_maps.active_operator.update_active_texture(context)

    def __surface_type_items__(
        self, context: bpy.types.Context
    ) -> List[Tuple[str, str, str, int]]:
        return [
            (s.name, s.pretty(), s.description(), s.value)
            # Constructed in this roundabout way to preserve natural order
            for s in SurfaceType
            if s in self.selected_surface_types()
        ]

    active_surface_type: bpy.props.EnumProperty(  # type: ignore
        name="Surface Type",
        default=SurfaceType.DRY.value,
        items=__surface_type_items__,
        update=__update_conditions__,
    )

    def get_active_surface_type(self) -> SurfaceType:
        return SurfaceType[self.active_surface_type]

    def __surface_age_items__(
        self, context: bpy.types.Context
    ) -> List[Tuple[str, str, str, int]]:
        return [(s.name, s.pretty(), s.description(), s.value) for s in SurfaceAge]

    active_surface_age: bpy.props.EnumProperty(  # type: ignore
        name="Surface Age",
        default=SurfaceAge.NEW.value,
        items=__surface_age_items__,
        update=__update_conditions__,
    )

    def update_sky_values(self) -> None:
        weather_ptr = self.get_active_weather()
        if weather_ptr is None:
            return
        if weather_ptr.world is None:
            return
        weather = weather_ptr.world.rbr_track_settings
        update_sky_vector(sky.SKY_FOG_COLOR, weather.fog_color)
        update_sky_value(sky.SKY_USE_FOG, weather.use_fog)
        update_sky_value(sky.SKY_GREENSTEIN_VALUE, weather.greenstein_value)
        update_sky_value(sky.SKY_INSCATTERING, weather.inscattering)
        update_sky_value(sky.SKY_MIE_MULTIPLIER, weather.mie_multiplier)
        update_sky_value(sky.SKY_RAYLEIGH_MULTIPLIER, weather.rayleigh_multiplier)
        update_sky_value(sky.SKY_SUN_INTENSITY, weather.sun_intensity)
        update_sky_value(sky.SKY_SUN_OFFSET, weather.sun_offset)
        update_sky_value(sky.SKY_SKYBOX_SATURATION, weather.skybox_saturation)
        update_sky_value(sky.SKY_SKYBOX_SCALE, weather.skybox_scale)
        update_sky_value(sky.SKY_SUPERBOWL_SCALE, weather.superbowl_scale)
        update_sky_value(sky.SKY_TURBIDITY, weather.turbidity)
        update_sky_value(sky.SKY_EXTINCTION, weather.extinction)
        update_sky_vector(
            sky.SKY_TERRAIN_REFLECTANCE_COLOR, weather.terrain_reflectance_color
        )
        update_sky_value(
            sky.SKY_TERRAIN_REFLECTANCE_MULTIPLIER,
            weather.terrain_reflectance_multiplier,
        )
        update_sky_value(sky.SKY_FOG_START, weather.fog_start)
        update_sky_value(sky.SKY_FOG_END, weather.fog_end)
        update_sky_value(sky.SKY_SUPERBOWL_FOG_START, weather.superbowl_fog_start)
        update_sky_value(sky.SKY_SUPERBOWL_FOG_END, weather.superbowl_fog_end)
        update_sky_value(sky.SKY_SPECULAR_GLOSSINESS, weather.specular_glossiness)
        update_sky_value(sky.SKY_SPECULAR_ALPHA, weather.specular_alpha)
        update_sun_dir()

    def get_active_surface_age(self) -> SurfaceAge:
        return SurfaceAge[self.active_surface_age]

    tint_set: bpy.props.EnumProperty(  # type: ignore
        name="Tint Set",
        description="Tint set",
        items=[(t.name, t.pretty(), t.pretty(), t.bitmask()) for t in TintSet],
        default=TintSet.MORNING.name,
        options=set(),
        update=lambda self, context: self.update_world_context(context),
    )

    def get_tint_set(self) -> TintSet:
        return TintSet[self.tint_set]

    # DEPRECATED
    overcast_time_of_day: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.pretty()) for t in TimeOfDay],
        default=TimeOfDay.MORNING.name,
    )
    # DEPRECATED
    # Old weathers, kept for migrations
    morning_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )
    noon_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )
    evening_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )
    overcast_morning_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )
    overcast_noon_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )
    overcast_evening_weathers: bpy.props.PointerProperty(  # type: ignore
        type=RBRWeathersDEPRECATED,
    )

    def update_world_context(self, context: bpy.types.Context) -> None:
        try:
            world_weather = self.world_weathers[self.active_world_weather]
            context.scene.world = world_weather.world
            weather_ptr = self.get_active_weather()
            if weather_ptr is None:
                return
            if weather_ptr.world is None:
                return
            setup_rbr_world(weather_ptr.world)
        except IndexError:
            pass

    world_weathers: bpy.props.CollectionProperty(  # type: ignore
        type=RBRWorldWeatherPtr,
    )
    active_world_weather: bpy.props.IntProperty(  # type: ignore
        update=lambda self, context: self.update_world_context(context),
    )

    def get_active_weather(self) -> Optional[RBRWorldWeatherPtr]:
        if self.active_world_weather < len(self.world_weathers):
            return self.world_weathers[self.active_world_weather]  # type: ignore
        return None

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
        layout.label(text="Weather Settings")
        layout.prop(self, "tint_set", expand=True)

        # List the weather slots
        world_list = layout.row()
        world_list.template_list(
            listtype_name="RBR_UL_world_weathers_list",
            list_id="",
            dataptr=self,
            propname="world_weathers",
            active_dataptr=self,
            active_propname="active_world_weather",
            rows=3,
        )
        # Buttons to add/remove weather slots
        right_buttons = world_list.column(align=True)
        right_buttons.operator(
            "rbr.add_world_weather_sky",
            icon="ADD",
            text="",
        )
        remove_button = right_buttons.operator(
            "rbr.remove_world_weather_sky",
            icon="REMOVE",
            text="",
        )
        remove_button.index = self.active_world_weather
        # Display the template_ID like UI for selecting what is in the active
        # slot
        try:
            active_world_weather = self.world_weathers[self.active_world_weather]
            layout.template_ID(active_world_weather, "world")
            if self.tint_set == TintSet.OVERCAST.name:
                layout.prop(active_world_weather, "overcast_time_of_day", text="Time")
        except IndexError:
            pass

        layout.label(text="Supported Surface Types")
        layout.prop(self, "surface_types")

        row = layout.row(align=True)
        row.label(text="Viewport")
        row.prop(self, "active_surface_type", text="")
        row.prop(self, "active_surface_age", text="")


class RBR_PT_track_settings(bpy.types.Panel):
    bl_idname = "RBR_PT_track_settings"
    bl_label = "RBR Track Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: bpy.types.Context) -> None:
        context.scene.rbr_track_settings.draw(context, self.layout)


class RBR_PT_world_track_settings(bpy.types.Panel):
    bl_idname = "RBR_PT_world_track_settings"
    bl_label = "RBR Track Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"

    def draw(self, context: bpy.types.Context) -> None:
        if context.world is not None:
            context.world.rbr_track_settings.draw(self.layout)


class RBR_UL_world_weathers_list(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: RBRTrackSettings,
        item: RBRWorldWeatherPtr,
        icon: int,
        _active_data: RBRTrackSettings,
        _active_propname: str,
    ) -> None:
        if item is None:
            return
        if item.world is None:
            return
        settings = item.world.rbr_track_settings
        layout.label(text=Weather[settings.weather].pretty())
        layout.label(text=Sky[settings.sky].pretty())
        layout.label(text=item.world.name)


@bpy.app.handlers.persistent  # type: ignore
def scene_change_daemon(scene: bpy.types.Scene) -> None:
    """Watch for scene changes and update the sky shaders accordingly"""
    try:
        last_scene = scene_change_daemon.last_scene
    except AttributeError:
        last_scene = None
    if last_scene != scene.name:
        scene.rbr_track_settings.update_sky_values()
    scene_change_daemon.last_scene = scene.name


def register() -> None:
    bpy.utils.register_class(RBRWorldWeatherPtr)
    bpy.utils.register_class(RBRWeatherSky)
    bpy.utils.register_class(RBRWeathersDEPRECATED)
    bpy.utils.register_class(RBRTrackSettings)
    bpy.utils.register_class(RBR_OT_add_world_weather_sky)
    bpy.utils.register_class(RBR_OT_remove_world_weather_sky)
    bpy.utils.register_class(RBR_UL_world_weathers_list)
    bpy.types.Scene.rbr_track_settings = bpy.props.PointerProperty(
        type=RBRTrackSettings,
    )
    bpy.types.World.rbr_track_settings = bpy.props.PointerProperty(
        type=RBRWeatherSky,
    )
    bpy.utils.register_class(RBR_PT_track_settings)
    bpy.utils.register_class(RBR_PT_world_track_settings)
    bpy.app.handlers.frame_change_pre.append(scene_change_daemon)


def unregister() -> None:
    bpy.app.handlers.frame_change_pre.remove(scene_change_daemon)
    bpy.utils.unregister_class(RBR_PT_world_track_settings)
    bpy.utils.unregister_class(RBR_PT_track_settings)
    del bpy.types.World.rbr_track_settings
    del bpy.types.Scene.rbr_track_settings
    bpy.utils.unregister_class(RBR_UL_world_weathers_list)
    bpy.utils.unregister_class(RBR_OT_remove_world_weather_sky)
    bpy.utils.unregister_class(RBR_OT_add_world_weather_sky)
    bpy.utils.unregister_class(RBRTrackSettings)
    bpy.utils.unregister_class(RBRWeathersDEPRECATED)
    bpy.utils.unregister_class(RBRWeatherSky)
    bpy.utils.unregister_class(RBRWorldWeatherPtr)
