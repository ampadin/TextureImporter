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

    

    @unreal.ufunction(static=True, params =[str], ret=bool, meta=dict(Category="TextureImporter"))
    def scan_material_parameters(master_material):
        return editor_api.scan_master_material_parameters(master_material)

    @unreal.ufunction(static=True, params=[str], ret=str, meta=dict(Category="TextureImporter"))
    def get_detected_parameter(texture_type):
        return editor_api.get_detected_parameter(texture_type)
    
    @unreal.ufunction(static=True, params=[str], ret=bool, meta=dict(Category="TextureImporter"))
    def is_parameter_matched(texture_type):
        return editor_api.is_parameter_matched(texture_type)

    @unreal.ufunction(static=True, params=[str], ret=bool, meta=dict(Category="TextureImporter"))
    def is_parameter_ambiguous(texture_type):
        return editor_api.is_parameter_ambiguous(texture_type)

    @unreal.ufunction(static=True, params=[str], ret=bool, meta=dict(Category="TextureImporter"))
    def is_parameter_name_valid(parameter_name):
        return editor_api.is_parameter_name_valid(parameter_name)
    
    @unreal.ufunction(static=True, ret=unreal.Array(str), meta=dict(Category="TextureImporter"))
    def get_last_scan_warnings():
        return editor_api.get_last_scan_warnings()    



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
    def get_default_import_emissive():
        return editor_api.get_default_import_emissive()
    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_import_opacity():
        return editor_api.get_default_import_opacity()

    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_overwrite():
        return editor_api.get_default_overwrite()
    @unreal.ufunction(static=True, ret=bool, meta=dict(Category="TextureImporter"))
    def get_default_flip_green():
        return editor_api.get_default_flip_green()

    # ---------------- Functions ----------------
    
    @unreal.ufunction(static=True,params=[str, str, str, str, bool, bool, bool, bool,bool, bool, bool,bool,bool,str,str,str,str,str,str,str,str,str], ret=bool, meta=dict(Category="TextureImporter"),)
    def run_import(source_folder, texture_root, material_root, master_material,
                    create_material_instance, create_orm, 
                    import_ao, import_roughness, import_metallic,
                    import_emissive, import_opacity,
                    flip_green, overwrite,
                    basecolor_parameter, normal_parameter, orm_parameter, height_parameter, ao_parameter, roughness_parameter, metallic_parameter, opacity_parameter, emissive_parameter):
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
            import_emissive=import_emissive,
            import_opacity=import_opacity,
            flip_green=flip_green,
            overwrite=overwrite,
            basecolor_parameter=basecolor_parameter,
            normal_parameter=normal_parameter, 
            orm_parameter= orm_parameter, 
            height_parameter=height_parameter, 
            ao_parameter=ao_parameter, 
            roughness_parameter=roughness_parameter, 
            metallic_parameter=metallic_parameter, 
            opacity_parameter=opacity_parameter,
            emissive_parameter=emissive_parameter,
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
