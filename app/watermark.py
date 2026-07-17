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
    tile_spacing: int = 0
    position_preset: PositionPreset = PositionPreset.CENTER
    custom_x: int = 0
    custom_y: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "Watermark":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:8]),
            wm_type=WatermarkType(data.get("wm_type", "image")),
            image_path=data.get("image_path", ""),
            text_content=data.get("text_content", "??"),
            font_size=data.get("font_size", 36),
            font_color=data.get("font_color", "#FFFFFF"),
            font_path=data.get("font_path", ""),
            opacity=data.get("opacity", 100),
            scale_percent=data.get("scale_percent", 100),
            rotation=data.get("rotation", 0),
            tiling_mode=TilingMode(data.get("tiling_mode", "none")),
            tile_spacing=data.get("tile_spacing", 0),
            position_preset=PositionPreset(data.get("position_preset", "center")),
            custom_x=data.get("custom_x", 0),
            custom_y=data.get("custom_y", 0),
        )

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
            "tile_spacing": self.tile_spacing,
            "position_preset": self.position_preset.value,
            "custom_x": self.custom_x,
            "custom_y": self.custom_y,
        }
