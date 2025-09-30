from typing import Dict


class PresetService:
    DEFAULT_PRESETS = {
        "Uniforme": {"ring1": 200, "ring2": 200, "ring3": 200, "ring4": 200},
        "Superior": {"ring1": 255, "ring2": 180, "ring3": 100, "ring4": 50},
        "Inferior": {"ring1": 50, "ring2": 100, "ring3": 180, "ring4": 255},
        "Centro": {"ring1": 80, "ring2": 200, "ring3": 200, "ring4": 80},
        "Suave": {"ring1": 100, "ring2": 100, "ring3": 100, "ring4": 100},
    }
    
    @classmethod
    def get_default_presets(cls) -> Dict[str, Dict[str, int]]:
        return cls.DEFAULT_PRESETS.copy()
