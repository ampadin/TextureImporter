from pathlib import Path
import json
from TI_Scripts.Core.Models.enums import TextureType
from TI_Scripts.Core.Models.plugin_settings import PluginSettings
from TI_Scripts.Core.Models.import_options import ImportOptions


TEXTURE_KEYS = {                                    #dictionary outside the code, constant
        TextureType.BASECOLOR: "BaseColor",
        TextureType.NORMAL: "Normal",
        TextureType.ORM: "ORM",
        TextureType.AO: "AO",
        TextureType.ROUGHNESS: "Roughness",
        TextureType.METALLIC: "Metallic",
        TextureType.HEIGHT: "Height",
        TextureType.OPACITY: "Opacity",         
        TextureType.EMISSIVE: "Emissive"        
        }                                       

class SettingsManager:
    #--------------Constructor -----------
    def __init__(self, plugin_root: Path | str):
        self.config_dir = Path(plugin_root) /"TI_Scripts" / "Config"

        self.validation_warnings =[]

        #loads  jsons
        self.naming_rules:dict = self._load_json("naming_rules.json")
        self.texture_rules:dict = self._load_json("texture_rules.json")
        self.material_parameters_rules:dict = self._load_json("material_parameter_rules.json")
        settings_json = self._load_json("plugin_settings.json")

        #loads and saves plugin_settings
        self.plugin_settings = PluginSettings(
            master_material=settings_json.get("masterMaterial", ""),
            create_material_instance= settings_json.get("createMaterialInstance", True),
            create_orm=settings_json.get("createORM", True),
            import_ao=settings_json.get("importAO",False),
            import_roughness=settings_json.get("importRoughness",False),
            import_metallic=settings_json.get("importMetallic",False),
            import_emissive=settings_json.get("importEmissive", True),
            import_opacity=settings_json.get("importOpacity", True),
            flip_green=settings_json.get("flipGreen", False),
            overwrite=settings_json.get("overwrite", False),
            save_assets=settings_json.get("saveAssets", True),
            supported_extensions=settings_json.get("supportedExtensions", []),
            material_parameters=settings_json.get("materialParameters",{}),
            texture_destination=settings_json.get("textureDestination", ""),
            material_destination=settings_json.get("materialDestination","")
        )

        self._supported_extensions = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in self.plugin_settings.supported_extensions}

        for texture_type, aliases in self.texture_rules.items():
            self.texture_rules[texture_type] = [alias.strip().lower() for alias in aliases]         #lowercase and strip whitespace to simplify comparisons

        parameter_aliases = (self.material_parameters_rules.get("parameterAliases",{}))
        for parameter_type, aliases in parameter_aliases.items():
            parameter_aliases[parameter_type] = [alias.strip().lower() for alias in aliases]

        parameter_prefixes = self.material_parameters_rules.get("parameterPrefixes",[])
        self.material_parameters_rules["parameterPrefixes"] = [prefix.strip().lower() for prefix in parameter_prefixes]
         
       
        self.validation_warnings.extend(self._validate())            #validation

#--------------- Functions and Propierties ---------------
    def _load_json(self, filename: str)-> dict:
        path = self.config_dir / filename
        if not path.exists():
            self.validation_warnings.append(f"Config file missing: {path}")
            return {}

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            self.validation_warnings.append(f"Cannot load JSON '{filename}': {e}")
            return {}


    def _validate(self) -> list[str]: 
        warnings = [] 
        if not self.naming_rules.get("prefix"): warnings.append("prefix missing in naming_rules.json")  
        if "suffixes" not in self.naming_rules: warnings.append("suffixes missing in naming_rules.json")
        if not self.plugin_settings.supported_extensions: warnings.append("No supported extensions defined")
        if not self.plugin_settings.master_material:  warnings.append("Master Material empty in plugins_settings.json")
        if not self.plugin_settings.texture_destination: warnings.append("Texture destination is empty in plugins_settings.json")
        if not self.plugin_settings.material_destination: warnings.append("Material destination is empty in plugins_settings.json")

        for texture_type in self.plugin_settings.material_parameters:
            if texture_type not in TextureType.__members__:
                warnings.append(f"Unknown material parameter '{texture_type}'")

        for key in TEXTURE_KEYS.values():
            if key not in self.texture_rules:  
                warnings.append(f"Warning: {key} has no aliases.")   ## This is part of the plugin's configuration


        parameter_aliases = (self.material_parameters_rules.get("parameterAliases"))
        if not isinstance(parameter_aliases, dict): warnings.append("parameterAliases missing or invalid in material_parameter_rules.json")
        else:
            for texture_type in TextureType:
                key = TEXTURE_KEYS.get(texture_type)
                if key is None: continue
                if key not in parameter_aliases: warnings.append(f"Warning: {key} has no material prameter aliases")

        parameter_prefixes = (self.material_parameters_rules.get("parameterPrefixes"))
        if not isinstance(parameter_prefixes, list): warnings.append("parameterPrefixes missing or invalid in material_parameter_rules.json")

        return warnings

    def _enum_to_json_key(self, texture_type: TextureType)->str:
        return TEXTURE_KEYS[texture_type]
            
    # -------------------------
    @property
    def master_material(self):
        return self.plugin_settings.master_material
    @property
    def create_orm(self):
        return self.plugin_settings.create_orm
    @property
    def import_ao(self):
        return self.plugin_settings.import_ao
    @property
    def import_roughness(self):
        return self.plugin_settings.import_roughness
    @property
    def import_metallic(self):
        return self.plugin_settings.import_metallic
    @property
    def import_emissive(self):
        return self.plugin_settings.import_emissive
    @property
    def import_opacity(self):
        return self.plugin_settings.import_opacity
    @property
    def flip_green(self):
        return self.plugin_settings.flip_green
    @property
    def overwrite(self):
        return self.plugin_settings.overwrite
    @property
    def save_assets(self):
        return self.plugin_settings.save_assets
    @property 
    def prefix(self):
            return self.naming_rules. get("prefix","") 
    @property
    def supported_extensions(self)-> set[str]:
        return self._supported_extensions
    @property
    def material_parameters(self):
        return {TextureType[key]: value for key, value in self.plugin_settings.material_parameters.items() if key in TextureType.__members__} 
    @property
    def has_warnings(self): return bool(self.validation_warnings)
    @property
    def texture_destination(self): return self.plugin_settings.texture_destination
    @property
    def material_destination(self): return self.plugin_settings.material_destination
    @property
    def create_material_instance(self): return self.plugin_settings.create_material_instance


    def get_suffix(self, texture_type:TextureType) -> str:
        key = self._enum_to_json_key(texture_type)
        return self.naming_rules.get("suffixes",{}).get(key,"")

    def get_aliases(self,texture_type:TextureType) -> list[str]:
            key = self._enum_to_json_key(texture_type)
            return self.texture_rules.get(key,[])
    
    def get_all_aliases(self)-> set[str]:
        aliases = set()
        for alias_list in self.texture_rules.values(): aliases.update(alias.lower() for alias in alias_list)
        return aliases

    def get_material_parameter_aliases(self,texture_type: TextureType)->list[str]:
        key = self._enum_to_json_key(texture_type)
        return self.material_parameters_rules.get("parameterAliases",{}).get(key,[])

    def get_material_parameter_prefixes(self)->list:
        return self.material_parameters_rules.get("parameterPrefixes",[])

    def create_default_import_options(self) ->ImportOptions:
        return ImportOptions(
                    master_material= self.master_material,
                    create_material_instance=self.create_material_instance,
                    material_parameters= self.material_parameters,
                    create_orm= self.create_orm,
                    import_ao= self.import_ao,
                    import_roughness= self.import_roughness,
                    import_metallic= self.import_metallic,
                    import_emissive= self.import_emissive,
                    import_opacity=self.import_opacity,
                    overwrite= self.overwrite,
                )