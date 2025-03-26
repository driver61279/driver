from typing import Any, Callable, Dict, List, Set, TypeVar, Union
import os
from zipfile import ZipFile

import bpy  # type: ignore

from rbr_track_formats import dls, errors, country_codes, tracks_ini
from rbr_track_formats.col import COL
from rbr_track_formats.dls import DLS, default_dls_section_order
from rbr_track_formats.dls.animation_sets import default_animation_set_section_order
from rbr_track_formats.errors import RBRAddonError
from rbr_track_formats.lbs import LBS
from rbr_track_formats.lbs.geom_blocks import RenderChunkDistance
from rbr_track_formats.track_settings import TrackFileName, TintSet
from rbr_track_formats.trk import TRK

from rbr_track_formats.serialise.col import col_to_binary
from rbr_track_formats.serialise.dls import dls_to_binary
from rbr_track_formats.serialise.fnc import fnc_to_binary
from rbr_track_formats.serialise.ini import to_ini
from rbr_track_formats.serialise.lbs import lbs_to_binary
from rbr_track_formats.serialise.mat import mat_to_binary
from rbr_track_formats.serialise.trk import trk_to_binary

import rbr_track_addon.blender_ops as ops
from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger
from rbr_track_addon.object_settings.types import RBRObjectSettings, RBRObjectType
from rbr_track_addon.preferences import DistStyle
from rbr_track_addon.track_settings import RBRTrackSettings

from . import components
from .util import KeyGen


class RBR_PT_export_settings(bpy.types.Panel):
    """A panel which just draws export settings"""

    bl_idname = "RBR_PT_export_settings"
    bl_label = "RBR Export Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: bpy.types.Context) -> None:
        # Always use scene 0 export settings - they apply for all tint sets.
        bpy.data.scenes[0].rbr_export_settings.draw(context, self.layout)
        self.layout.operator(RBR_OT_export_track.bl_idname, text="Export")


class RBRExportSettings(bpy.types.PropertyGroup):
    """All settings for exporting the track. Allows the user to select which
    objects to export and how to export them. This data is saved in the blend
    file for convenience.
    """

    export_to: bpy.props.StringProperty(  # type: ignore
        name="Export to",  # noqa: F821
    )

    track_id: bpy.props.IntProperty(  # type: ignore
        name="ID",  # noqa: F821
        description="Track number (e.g. 71 for rally school)",
    )

    track_name: bpy.props.StringProperty(  # type: ignore
        name="Track Name",  # noqa: F821
        description="Track name (e.g. Rally School)",
    )

    author: bpy.props.StringProperty(  # type: ignore
        name="Author",  # noqa: F821
        description="Track author",
    )

    particles: bpy.props.StringProperty(  # type: ignore
        name="Particles",  # noqa: F821
        description="Particles used in the stage",
        default="ps_british",  # noqa: F821
    )

    surface: bpy.props.EnumProperty(  # type: ignore
        name="Surface",  # noqa: F821
        items=[
            (t.name, t.pretty(), t.pretty(), t.value) for t in tracks_ini.StageSurface
        ],
        default=tracks_ini.StageSurface.TARMAC.name,
    )

    country: bpy.props.EnumProperty(  # type: ignore
        name="Country",  # noqa: F821
        items=[
            (t.alpha_2_code, t.alpha_2_code, t.country, t.numeric)
            for t in sorted(country_codes.country_codes, key=lambda t: t.alpha_2_code)
        ],
        default="GB",  # noqa: F821
    )

    cleanup: bpy.props.BoolProperty(  # type: ignore
        name="Cleanup Temporary Objects",  # noqa: F821
        description="Remove any objects created during export",
        default=True,
    )

    export_lbs: bpy.props.BoolProperty(  # type: ignore
        name="lbs, trk, ini, rbz",  # noqa: F821
        description="Visual geometry, car location, driveline, shape collisions, clipping planes",
        default=True,
    )

    chunk_size: bpy.props.FloatProperty(  # type: ignore
        name="Chunk Size",
        description="Larger chunks might give more FPS but increase chance of pop-in",
        default=100.0,
        min=50.0,
        max=250.0,
    )

    export_col: bpy.props.BoolProperty(  # type: ignore
        name="col, mat",  # noqa: F821
        description="Ground collision mesh, brake wall, physical materials",
        default=True,
    )

    export_dls: bpy.props.BoolProperty(  # type: ignore
        name="dls",  # noqa: F821
        description="Cameras, pacenotes, render distance",
        default=True,
    )

    export_tracks_ini: bpy.props.BoolProperty(  # type: ignore
        name="Tracks.ini",  # noqa: F821
        default=True,
    )

    export_track_settings: bpy.props.BoolProperty(  # type: ignore
        name="TrackSettings.ini",  # noqa: F821
        default=True,
    )

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
        prefs = context.preferences.addons["rbr_track_addon"].preferences
        layout.prop_search(
            self,
            "export_to",
            prefs,
            "export_directories",
        )
        layout.prop(self, "track_id")
        layout.prop(self, "track_name")
        layout.prop(self, "author")
        layout.prop(self, "particles")
        layout.prop(self, "surface")
        layout.prop(self, "country")
        layout.label(
            text="Track Name: "
            + TrackFileName(
                track_id=self.track_id,
                tint_set=TintSet[context.scene.rbr_track_settings.tint_set],
            ).serialise()
        )
        layout.prop(self, "cleanup")
        parts = layout.box()
        parts.prop(self, "export_lbs")
        if self.export_lbs:
            parts.prop(self, "chunk_size", slider=True)
        parts.prop(self, "export_col")
        parts.prop(self, "export_dls")
        parts.prop(self, "export_tracks_ini")
        parts.prop(self, "export_track_settings")


def partition_view_layer_objects() -> Dict[RBRObjectType, List[TracedObject]]:
    """Partition any object in the view layer by object type, for exporting.
    Ignores objects hidden in the view layer, and objects not marked for
    export. Applies instancers."""
    objs: Dict[RBRObjectType, List[TracedObject]] = dict()
    for obj in bpy.context.view_layer.objects:
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        if not object_settings.exported:
            continue
        if not obj.visible_get():
            continue
        obj_type = RBRObjectType[object_settings.type]
        try:
            objs[obj_type].append(TracedObject.create(obj))
        except KeyError:
            objs[obj_type] = [TracedObject.create(obj)]
    # Apply instancers
    if RBRObjectType.INSTANCER in objs:
        instancers = objs[RBRObjectType.INSTANCER]
        for instancer in instancers:
            reals = ops.duplicates_make_real(instancer)
            for real in reals:
                obj_type = RBRObjectType[real.obj.rbr_object_settings.type]
                try:
                    objs[obj_type].append(real)
                except KeyError:
                    objs[obj_type] = [real]
    return objs


class RBR_OT_export_track(bpy.types.Operator):
    """Export an RBR track"""

    bl_idname = "rbr.export_track"
    bl_label = "Export RBR track"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return context.window_manager.invoke_props_dialog(self)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        logger = Logger()
        try:
            export_restoring_data_blocks(context, logger)
            self.report({"INFO"}, "Export completed")
            return {"FINISHED"}
        except RBRAddonError as e:
            lang = context.preferences.addons[
                "rbr_track_addon"
            ].preferences.get_language()
            self.report({"ERROR"}, e.report(lang))
            return {"FINISHED"}

    @classmethod
    def poll(_cls, context: bpy.types.Context) -> bool:
        settings = bpy.data.scenes[0].rbr_export_settings
        return settings.export_to != ""  # type: ignore

    def draw(self, context: bpy.types.Context) -> None:
        settings = bpy.data.scenes[0].rbr_export_settings
        layout = self.layout.box()
        prefs = context.preferences.addons["rbr_track_addon"].preferences
        layout.prop_search(
            settings,
            "export_to",
            prefs,
            "export_directories",
        )
        layout.prop(context.scene.rbr_track_settings, "tint_set")
        row = layout.row()
        row.label(
            text=TrackFileName(
                track_id=settings.track_id,
                tint_set=TintSet[context.scene.rbr_track_settings.tint_set],
            ).serialise()
        )
        row.prop(settings, "track_id")


A = TypeVar("A")


def export_restoring_data_blocks(
    context: bpy.types.Context,
    logger: Logger,
) -> None:
    source_data = [
        bpy.data.meshes,
        bpy.data.objects,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.materials,
        bpy.data.node_groups,
        bpy.data.lights,
        bpy.data.actions,
        bpy.data.collections,
    ]
    saved_data = []
    logger.info("Saving ID blocks")
    for source in source_data:
        saved = set()
        for x in source:
            saved.add(x.name_full)
        saved_data.append(saved)
    try:
        run_export(context, logger)
    finally:
        settings: RBRExportSettings = bpy.data.scenes[0].rbr_export_settings
        if settings.cleanup:
            logger.info("Restoring ID blocks")
            for source, saved in zip(source_data, saved_data):
                for x in source:
                    if x.name_full not in saved:
                        try:
                            source.remove(x)
                        except Exception:
                            pass
        else:
            logger.info("Not restoring ID blocks because 'cleanup' is false")


def run_export(
    context: bpy.types.Context,
    logger: Logger,
) -> None:
    # Try to switch to object mode, we can't export from edit mode
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        pass

    settings: RBRExportSettings = bpy.data.scenes[0].rbr_export_settings

    track_settings: RBRTrackSettings = bpy.context.scene.rbr_track_settings
    tint_set = track_settings.get_tint_set()

    track_file_name = TrackFileName(
        track_id=settings.track_id,
        tint_set=tint_set,
    ).serialise()

    objects_dict = partition_view_layer_objects()
    keygen = KeyGen()

    prefs = context.preferences.addons["rbr_track_addon"].preferences
    export_directory = prefs.get_export_directory(settings.export_to)
    if export_directory is None:
        raise errors.E0105(export_name=settings.export_to)
    (export_directory, dist_style) = export_directory
    track_dir = "Maps"
    track_sub_dir = (
        f"{settings.track_id}-{tracks_ini.sanitise_stage_name(settings.track_name)}"
    )
    if dist_style is DistStyle.RSF:
        export_directory = os.path.join(export_directory, track_sub_dir)
        track_dir = os.path.join("Maps", track_sub_dir)
        try:
            os.mkdir(export_directory)
        except FileExistsError:
            pass

    def write_format(
        writemode: str,
        extension: str,
        format: A,
        encode: Union[Callable[[A], bytes], Callable[[A], str]],
        file_name: str = track_file_name,
    ) -> None:
        def run_export() -> None:
            path = os.path.join(export_directory, file_name + "." + extension)
            abs_path = bpy.path.abspath(path)
            with open(abs_path, writemode) as f:
                f.write(encode(format))

        return logger.section(
            f"Writing {extension}",
            run_export,
        )

    def objs_list(t: RBRObjectType) -> List[TracedObject]:
        dupes = objects_dict.get(t)
        if dupes is None:
            return []
        else:
            return dupes

    driveline_objs = objs_list(RBRObjectType.DRIVELINE)
    if len(driveline_objs) != 1:
        raise errors.E0148()
    driveline_obj = driveline_objs[0]

    if settings.export_tracks_ini:
        length = components.driveline.compute_stage_length(driveline_obj)
        ini = tracks_ini.TracksINI(
            track_id=settings.track_id,
            track_dir=track_dir,
            particles=settings.particles,
            stage_name=settings.track_name,
            surface=tracks_ini.StageSurface[settings.surface],
            country_code=settings.country,
            length=length,
            author=settings.author,
            splash_screen_path=f"Textures\\Splash\\{track_sub_dir}.dds",
        )
        write_format(
            "w",
            "ini",
            ini.serialise(),
            lambda x: x,
            file_name=f"Tracks{settings.track_id}",
        )

    export_texture_oracle = logger.section(
        "Collecting RBR materials",
        lambda: components.textures.RBRExportTextureOracle(logger),
    )

    if settings.export_lbs:
        car_location = logger.section(
            "Car location",
            lambda: components.car_location.export_car_location(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.CAR_LOCATION),
            ),
        )

        def filter_invisible(objs: List[TracedObject]) -> List[TracedObject]:
            def f(traced_obj: TracedObject) -> bool:
                ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
                # Don't export geom blocks marked as invisible, they should
                # only get collision meshes.
                if ros.is_geom_blocks_collision and ros.is_geom_blocks_invisible:
                    return False
                return True

            return list(filter(f, objs))

        world_chunks = logger.section(
            "World chunks",
            lambda: components.geom_blocks.export_world_chunks(
                export_texture_oracle=export_texture_oracle,
                logger=logger,
                # Typical vanilla stages have square chunks with 100m sides
                chunk_size=settings.chunk_size,
                geom_block_objects=filter_invisible(
                    objs_list(RBRObjectType.GEOM_BLOCKS)
                ),
                object_block_objects=objs_list(RBRObjectType.OBJECT_BLOCKS),
            ),
        )

        super_bowl = logger.section(
            "Super bowl",
            lambda: components.super_bowl.export_super_bowl(
                export_texture_oracle=export_texture_oracle,
                logger=logger,
                traced_objs=objs_list(RBRObjectType.SUPER_BOWL),
            ),
        )

        reflection_objects = logger.section(
            "Reflection objects",
            lambda: components.reflection_objects.export_reflection_objects(
                export_texture_oracle=export_texture_oracle,
                logger=logger,
                traced_objs=objs_list(RBRObjectType.REFLECTION_OBJECTS),
            ),
        )

        water_objects = logger.section(
            "Water objects",
            lambda: components.water_objects.export_water_objects(
                export_texture_oracle=export_texture_oracle,
                logger=logger,
                traced_input_objs=objs_list(RBRObjectType.WATER_OBJECTS),
            ),
        )

        clipping_planes = logger.section(
            "Clipping planes",
            lambda: components.clipping_planes.export_clipping_planes(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.CLIPPING_PLANE),
            ),
        )

        (interactive_scms, interactive_objects) = logger.section(
            "Interactive objects",
            lambda: components.interactive_objects.export_interactive_objects(
                export_texture_oracle=export_texture_oracle,
                logger=logger,
                keygen=keygen,
                traced_objs=objs_list(RBRObjectType.INTERACTIVE_OBJECTS),
            ),
        )

        lbs = LBS(
            world_chunks=world_chunks,
            clipping_planes=clipping_planes,
            car_location=car_location,
            drive_points=None,
            interactive_objects=interactive_objects,
            reflection_objects=reflection_objects,
            water_objects=water_objects,
            super_bowl=super_bowl,
            track_loader_vecs=None,  # TODO
            animation_objects=None,  # TODO
            container_objects=None,  # TODO
            unhandled_segments=dict(),
        )
        write_format(
            "wb",
            "lbs",
            lbs,
            lbs_to_binary,
        )

        driveline = logger.section(
            "Driveline",
            lambda: components.driveline.export_driveline(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.DRIVELINE),
            ),
        )

        shape_collision_meshes = logger.section(
            "Shape collision meshes",
            lambda: components.shape_collision_meshes.export_shape_collision_meshes(
                keygen=keygen,
                logger=logger,
                traced_objs=objs_list(RBRObjectType.SHAPE_COLLISION_MESH),
            ),
        )

        trk = TRK(
            driveline=driveline,
            shape_collision_meshes=interactive_scms.union(shape_collision_meshes),
        )
        write_format(
            "wb",
            "trk",
            trk,
            trk_to_binary,
        )

        def run_texture_export() -> None:
            rbz_name = track_file_name + "_textures"
            path = os.path.join(export_directory, rbz_name + ".rbz")
            abs_path = bpy.path.abspath(path)
            with ZipFile(abs_path, "w") as rbz:
                ini = export_texture_oracle.export_textures_ini(rbz, rbz_name)
                write_format("w", "ini", ini, to_ini)

        logger.section(
            "Textures (.ini and .rbz)",
            run_texture_export,
        )

    if settings.export_track_settings:
        track_settings_ini = components.track_settings.export_track_settings(
            logger=logger,
            track_id=settings.track_id,
            traced_suns=objs_list(RBRObjectType.SUN),
        )
        write_format(
            "w",
            "ini",
            track_settings_ini,
            lambda x: x,
            file_name=f"TrackSettings{settings.track_id}",
        )

    if settings.export_dls:
        camera_data = logger.section(
            "Cameras",
            lambda: components.cameras.export_cameras(
                keygen=keygen,
                logger=logger,
                traced_objs=objs_list(RBRObjectType.CAMERA),
            ),
        )

        pacenotes = logger.section(
            "Pacenotes",
            lambda: components.driveline.export_pacenotes(
                traced_driveline_obj=driveline_obj,
            ),
        )

        registration_zone = logger.section(
            "Registration Zone",
            lambda: components.registration_zone.export_registration_zone(
                traced_objs=objs_list(RBRObjectType.REGISTRATION_ZONE),
            ),
        )

        sound_emitters = logger.section(
            "Sound Triggers",
            lambda: components.sound_emitters.export_sound_emitters(
                traced_objs=objs_list(RBRObjectType.SOUND_EMITTER),
            ),
        )

        zfar = logger.section(
            "ZFAR",
            lambda: components.zfar.export_zfar(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.ZFAR),
                traced_driveline_obj=driveline_obj,
            ),
        )

        driveline_set = dls.animation_sets.AnimationSet(
            name="Driveline",
            sig_trigger_data=[],
            section_channels=[],
            animation_channels=[],  # TODO
            bool_channels=[],  # TODO
            real_channels=[],
            pacenotes=[],
        )
        dls_file = DLS(
            animation_sets=dls.animation_sets.AnimationSets([driveline_set]),
            trigger_data=dls.trigger_data.TriggerData(dict()),
            splines=dls.splines.Splines([]),
            animation_cameras=dls.animation_cameras.AnimationCameras(dict()),
            track_emitters=dls.track_emitters.TrackEmitters([]),  # TODO
            helicams=dls.helicams.Helicams([]),  # TODO
            sound_emitters=dls.sound_emitters.SoundEmitters([]),
            registration_zone=None,
            animation_ids=dls.animation_ids.AnimationIDs(dict()),  # TODO
        )

        dls_file.section_order = default_dls_section_order()
        dls_file.extra_names = dict()
        for anim_set in dls_file.animation_sets.sets:
            anim_set.section_order = default_animation_set_section_order()

        if pacenotes is not None:
            driveline_set.pacenotes = pacenotes
        if camera_data is not None:
            (
                anim_cameras,
                trigger_data,
                sig_trigger_data,
                section_channels,
                real_channels,
                splines,
            ) = camera_data
            dls_file.trigger_data = trigger_data
            dls_file.animation_cameras = anim_cameras
            dls_file.splines = splines
            driveline_set.sig_trigger_data = sig_trigger_data
            driveline_set.section_channels = section_channels
            driveline_set.real_channels = real_channels
        if registration_zone is not None:
            dls_file.registration_zone = registration_zone
        if sound_emitters is not None:
            dls_file.sound_emitters = sound_emitters
        if zfar is not None:
            driveline_set.set_real_channel(zfar)
        write_format(
            "wb",
            "dls",
            dls_file,
            dls_to_binary,
        )

    fnc_file = logger.section(
        "Fences",
        lambda: components.fences.export_fnc(
            logger=logger,
            traced_objs=objs_list(RBRObjectType.FENCE),
        ),
    )
    write_format(
        "wb",
        "fnc",
        fnc_file,
        fnc_to_binary,
    )

    if settings.export_col:
        (material_oracle, mat) = logger.section(
            "Material maps",
            lambda: components.collision_mesh.export_physical_materials(
                context=context,
            ),
        )

        def filter_col(traced_objs: List[TracedObject]) -> List[TracedObject]:
            def f(traced_obj: TracedObject) -> bool:
                ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
                if not ros.is_geom_blocks_collision:
                    return False
                # Don't let far objects get collision meshes.
                if ros.geom_blocks_distance == RenderChunkDistance.FAR.name:
                    return False
                return True

            return list(filter(f, traced_objs))

        colmesh = logger.section(
            "Static colmesh",
            lambda: components.collision_mesh.export_world_colmesh(
                logger=logger,
                traced_objs=filter_col(objs_list(RBRObjectType.GEOM_BLOCKS)),
                material_oracle=material_oracle,
                mat=mat,
            ),
        )
        (root, subtrees, packed_mat) = colmesh

        write_format("wb", "mat", packed_mat, mat_to_binary)

        brake_wall = logger.section(
            "Brake wall",
            lambda: components.brake_wall.export_brake_wall(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.BRAKE_WALL),
            ),
        )

        (wet_surfaces, water_surfaces) = logger.section(
            "Wet surfaces",
            lambda: components.wet_surfaces.export_wet_surfaces(
                logger=logger,
                traced_objs=objs_list(RBRObjectType.WET_SURFACE),
            ),
        )

        col = COL(
            brake_wall=brake_wall,
            wet_surfaces=wet_surfaces,
            water_surfaces=water_surfaces,
            collision_tree_root=root,
            subtrees=subtrees,
        )
        write_format(
            "wb",
            "col",
            col,
            col_to_binary,
        )

    logger.info("Export done")


def export_menu_func(self: Any, context: bpy.types.Context) -> None:
    self.layout.operator(RBR_OT_export_track.bl_idname, text="RBR Track")


def register() -> None:
    bpy.utils.register_class(RBRExportSettings)
    bpy.types.BlendData.rbr_export_settings = bpy.props.PointerProperty(
        type=RBRExportSettings,
    )
    bpy.types.Scene.rbr_export_settings = bpy.props.PointerProperty(
        type=RBRExportSettings,
    )
    bpy.utils.register_class(RBR_PT_export_settings)
    bpy.utils.register_class(RBR_OT_export_track)
    bpy.types.TOPBAR_MT_file_export.append(export_menu_func)


def unregister() -> None:
    bpy.types.TOPBAR_MT_file_export.remove(export_menu_func)
    bpy.utils.unregister_class(RBR_OT_export_track)
    bpy.utils.unregister_class(RBR_PT_export_settings)
    del bpy.types.Scene.rbr_export_settings
    del bpy.types.BlendData.rbr_export_settings
    bpy.utils.unregister_class(RBRExportSettings)
