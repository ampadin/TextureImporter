import unreal
import tkinter as tk
from tkinter import filedialog

from TI_Scripts.Unreal import editor_api


@unreal.uclass()
class TIBlueprintLibrary(unreal.BlueprintFunctionLibrary):

    # ---------------- Defaults ----------------

    @unreal.ufunction(static=True, ret=str, meta=dict(Category="TextureImporter"))
    def get_default_master_material():
        return editor_api.get_default_master_material()

    @unreal.ufunction(static=True, ret=str, meta=dict(Category="TextureImporter"))
    def get_default_texture_destination():
        return editor_api.get_default_texture_destination()

    @unreal.ufunction(static=True, ret=str, meta=dict(Category="TextureImporter"))
    def get_default_material_destination():
        return editor_api.get_default_material_destination()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_create_material_instance():
        return editor_api.get_default_create_material_instance()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_create_orm():
        return editor_api.get_default_create_orm()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_import_ao():
        return editor_api.get_default_import_ao()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_import_roughness():
        return editor_api.get_default_import_roughness()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_import_metallic():
        return editor_api.get_default_import_metallic()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_overwrite():
        return editor_api.get_default_overwrite()

    # ---------------- Functions ----------------

    @unreal.ufunction(
        static=True,
        params=[str, str, str, str, bool, bool, bool, bool, bool, bool],
        ret=bool,
        meta=dict(Category="TextureImporter"),
    )
    def run_import(source_folder, texture_root, material_root, master_material,
                    create_material_instance, create_orm, import_ao,
                    import_roughness, import_metallic, overwrite):
        return editor_api.run_import(
            source_folder=source_folder,
            texture_root=texture_root,
            material_root=material_root,
            master_material=master_material,
            create_material_instance=create_material_instance,
            create_orm=create_orm,
            import_ao=import_ao,
            import_roughness=import_roughness,
            import_metallic=import_metallic,
            overwrite=overwrite,
        )

    # ---------------- Last import result ----------------
    @unreal.ufunction(static=True, ret=str, meta=dict(Category="TextureImporter"))
    def get_last_import_status_text():
        return editor_api.get_last_import_status_text()

    
    @unreal.ufunction(static=True, ret=str, meta=dict(Category="TextureImporter"))
    def write_last_import_log():
        return editor_api.write_last_log()
    
    # ----------------Open file explorer ----------------

    @unreal.ufunction(static=True, params=[str], ret=str, meta=dict(Category="TextureImporter"))
    def browse_folder(start_directory):
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)               # keeps the dialog always on top
            folder = filedialog.askdirectory(initialdir=start_directory, title="Select Source Folder")
            root.destroy()
            return folder if folder else ""
        except Exception as e:
            unreal.log_error(f"Browse_folder failed: {e}")
            return ""
