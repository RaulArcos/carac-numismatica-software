PresetValues = dict[str, int]


def _create_uniform_preset(intensity: int) -> PresetValues:
    return {
        f"ring{ring}_section{section}": intensity
        for ring in range(1, 5)
        for section in range(1, 5)
    }


def _create_section_preset(section_intensities: list[int]) -> PresetValues:
    return {
        f"ring{ring}_section{section}": section_intensities[section - 1]
        for ring in range(1, 5)
        for section in range(1, 5)
    }


class PresetService:
    DEFAULT_PRESETS: dict[str, PresetValues] = {
        "Uniforme": _create_uniform_preset(200),
        "Brillante": _create_uniform_preset(255),
        "Suave": _create_uniform_preset(100),
        "Derecha-Izquierda": _create_section_preset([200, 80, 200, 80]),
        "Frente-Atrás": _create_section_preset([80, 200, 80, 200]),
        "Diagonal": _create_section_preset([200, 100, 200, 100]),
    }

    @classmethod
    def get_default_presets(cls) -> dict[str, PresetValues]:
        return {name: preset.copy() for name, preset in cls.DEFAULT_PRESETS.items()}
