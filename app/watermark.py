import uuid
from enum import Enum
from dataclasses import dataclass, field


class WatermarkType(Enum):
    IMAGE = "image"
    TEXT = "text"


class TilingMode(Enum):
    NONE = "none"
    TILE = "tile"
    FILL = "fill"


class PositionPreset(Enum):
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"
    CUSTOM = "custom"


@dataclass
class Watermark:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    wm_type: WatermarkType = WatermarkType.IMAGE
    image_path: str = ""
    text_content: str = "水印"
    font_size: int = 36
    font_color: str = "#FFFFFF"
    font_path: str = ""

    opacity: int = 100
    scale_percent: int = 100
    rotation: int = 0
    tiling_mode: TilingMode = TilingMode.NONE
    position_preset: PositionPreset = PositionPreset.CENTER
    custom_x: int = 0
    custom_y: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "wm_type": self.wm_type.value,
            "image_path": self.image_path,
            "text_content": self.text_content,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "font_path": self.font_path,
            "opacity": self.opacity,
            "scale_percent": self.scale_percent,
            "rotation": self.rotation,
            "tiling_mode": self.tiling_mode.value,
            "position_preset": self.position_preset.value,
            "custom_x": self.custom_x,
            "custom_y": self.custom_y,
        }
