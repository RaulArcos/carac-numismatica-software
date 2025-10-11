PresetValues = dict[str, int]


class PresetService:
    @staticmethod
    def _create_uniform_preset(intensity: int) -> PresetValues:
        """Create a preset with uniform intensity across all rings and sections"""
        preset = {}
        for ring in range(1, 5):
            for section in range(1, 5):
                preset[f"ring{ring}_section{section}"] = intensity
        return preset
    
    @staticmethod
    def _create_section_preset(section_intensities: list[int]) -> PresetValues:
        """Create a preset where each section has the same intensity across all rings"""
        preset = {}
        for ring in range(1, 5):
            for section in range(1, 5):
                preset[f"ring{ring}_section{section}"] = section_intensities[section - 1]
        return preset
    
    @staticmethod
    def _create_ring_preset(ring_intensities: list[int]) -> PresetValues:
        """Create a preset where each ring has uniform intensity across all sections"""
        preset = {}
        for ring in range(1, 5):
            for section in range(1, 5):
                preset[f"ring{ring}_section{section}"] = ring_intensities[ring - 1]
        return preset
    
    DEFAULT_PRESETS: dict[str, PresetValues] = {
        "Uniforme": _create_uniform_preset.__func__(200),
        "Brillante": _create_uniform_preset.__func__(255),
        "Suave": _create_uniform_preset.__func__(100),
        "Derecha-Izquierda": _create_section_preset.__func__([200, 80, 200, 80]),
        "Frente-Atrás": _create_section_preset.__func__([80, 200, 80, 200]),
        "Diagonal": _create_section_preset.__func__([200, 100, 200, 100]),
    }

    @classmethod
    def get_default_presets(cls) -> dict[str, PresetValues]:
        return {name: preset.copy() for name, preset in cls.DEFAULT_PRESETS.items()}
