import unreal

from TI_Scripts.Core.Models.enums import TextureType

from TI_Scripts.Core.Python.settings import SettingsManager

class MaterialParameterDetector:
    def __init__(self, settings: SettingsManager): 
        self.settings = settings

    def _normalize_parameter_name(self,name:str)->str:
        normalized = name.strip().lower()

        for separator in ("_", "-", " "):
            normalized = normalized.replace(separator, "")

        prefixes = self.settings.get_material_parameter_prefixes()

        for prefix in prefixes:
            normalized_prefix = (prefix.strip().lower())
            normalized_prefix = (normalized_prefix.replace("_","").replace("-","").replace(" ",""))
            if normalized.startswith(normalized_prefix) and len(normalized) > len(normalized_prefix):
                normalized = normalized[len(normalized_prefix):]
                break
            
        return normalized

    def _find_candidates(self, parameter_name:str) ->list[TextureType]:
        normalized_name = self._normalize_parameter_name(parameter_name)
        candidates: list[TextureType] = []

        for texture_type in TextureType:
            if texture_type is TextureType.UNKNOWN: continue
            aliases = (self.settings.get_material_parameter_aliases(texture_type))
            normalized_aliases = {self._normalize_parameter_name(alias) for alias in aliases}

            if normalized_name in normalized_aliases:
                candidates.append(texture_type)
        return candidates

    def get_material_texture_parameters(self, master_material:str, default_parameters:dict[TextureType,str]|None = None) ->dict:
        """
        Reads texture parameter names from a Master Material and attempts
        to map them automatically to the supported TextureTypes.
        The function does not modify the Material or any project asset.
        Returns:
            {
                "success": bool,
                "parameters": dict[TextureType, str],
                "matched":dict[TextureType,bool], #TRUE only for autodetected matches
                "ambiguous":dict[TextureType,bool],
                "warnings": list[str],
                "errors": list[str],
            }
        """
        material = unreal.load_asset(master_material)

        if material is None:
            return {
                "success": False,
                "parameters": default_parameters or {},
                "matched":{},
                "ambiguous":{},
                "warnings": [],
                "errors": [f"Cannot load Master Material '{master_material}'."]
            }

        try:
            parameter_names = (unreal.MaterialEditingLibrary.get_texture_parameter_names(material))
        except Exception as exc:
            return {
                "success": False,
                "parameters": default_parameters or {},
                "matched":{},
                "ambiguous":{},
                "warnings": [f"Using default texture parmeter name sfound in plugin_settings.json."],
                "errors": [f"Cannot read texture parameters from Master Material '{master_material}': {exc}"],
            }

#START EMPTY SO DETECTED VALUES OVERRIDE FEFAULTS: Defaults are added afterwards as fallback.
        parameters: dict[TextureType,str] = {}
        matched: dict[TextureType,bool] = {}
        ambiguous: dict[TextureType,bool] = {}
        warnings:list[str] = []

        for parameter_name in parameter_names: 
            parameter_name = str(parameter_name)
            candidates = self._find_candidates(parameter_name)

        #Allow only one match
            if len(candidates) == 1:
                texture_type = candidates[0]

                #Do not silently replace a parameter if another one was already detected for the same texture type
                if texture_type in parameters and parameters[texture_type]:
                    warnings.append(f"Multiple '{texture_type.name}' texture parameters detected."
                                    f"'{parameters[texture_type]}' was already assigned, {parameter_name} was not selected.")
                    ambiguous[texture_type] = True
                    continue

                parameters[texture_type] = parameter_name
                matched[texture_type] = True

            elif len(candidates)>1:
                candidate_names = ", ".join(texture_type.name for texture_type in candidates)
                warnings.append(f"parameter '{parameter_name}' matches multiple texture types: {candidate_names}. Automatic assigment skipped.")

        for texture_type,default_value in (default_parameters or {}).items():
            if  (texture_type not in parameters and default_value):
                parameters[texture_type] = default_value
                matched[texture_type] = False
            
        return{
            "success":True,
            "parameters": parameters,
            "matched": matched,
            "ambiguous": ambiguous,
            "warnings": warnings,
            "errors": [],
        }