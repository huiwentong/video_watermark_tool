import cv2
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
from typing import Optional, Tuple, List
from app.watermark import Watermark, WatermarkType, TilingMode, PositionPreset
import os


def _find_chinese_font() -> str:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/yahei.ttf",
        "C:/Windows/Fonts/Deng.ttf",
        "C:/Windows/Fonts/STKAITI.TTF",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    try:
        for f in os.listdir("C:/Windows/Fonts"):
            if f.lower().endswith((".ttf", ".ttc")):
                full = os.path.join("C:/Windows/Fonts", f)
                if os.path.isfile(full):
                    return full
    except Exception:
        pass
    return ""


class WatermarkRenderer:
    """Preview rendering engine -- composite watermarks onto video frames"""

    def __init__(self, video_path: str = ""):
        self.video_path = video_path
        self._frame: Optional[np.ndarray] = None
        self.ori_wm_composite: Optional[PILImage.Image] = None
        self._frame_pil: Optional[PILImage.Image] = None
        self.video_width: int = 0
        self.video_height: int = 0
        self._chinese_font_path = _find_chinese_font()
        self._is_image_source: bool = False
        self._source_image_path: str = ""
        self._video_fps: float = 0.0
        self._total_frames: int = 0

    def load_frame(self, video_path: Optional[str] = None, time_sec: float = 0.0) -> bool:
        if video_path:
            self.video_path = video_path
        if not self.video_path:
            return False
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return False
        fps = cap.get(cv2.CAP_PROP_FPS)
        self._video_fps = fps
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = int(time_sec * fps) if fps > 0 else 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, self._frame = cap.read()
        cap.release()
        if not ret or self._frame is None:
            return False
        self.video_height, self.video_width = self._frame.shape[:2]
        self._frame_pil = PILImage.fromarray(cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB))
        self._is_image_source = False
        return True

    def load_image(self, image_path: str) -> bool:
        if not os.path.isfile(image_path):
            return False
        try:
            self._source_image_path = image_path
            self._frame_pil = PILImage.open(image_path).convert("RGBA")
            self.video_width, self.video_height = self._frame_pil.size
            self._frame = np.array(self._frame_pil)
            self._is_image_source = True
            return True
        except Exception:
            return False

    def get_total_frames(self) -> int:
        return self._total_frames

    def get_video_fps(self) -> float:
        return self._video_fps

    def is_image_source(self) -> bool:
        return self._is_image_source

    def get_frame_size(self) -> Tuple[int, int]:
        return self.video_width, self.video_height

    def render_preview(self, watermarks: List[Watermark]) -> Optional[PILImage.Image]:
        if self._frame_pil is None:
            return None
        frame = self._frame_pil.copy().convert("RGBA")
        for wm in watermarks:
            if wm.wm_type == WatermarkType.IMAGE:
                wm_img = self._render_image_watermark(wm, frame.size)
            else:
                wm_img = self._render_text_watermark(wm, frame.size)
            if wm_img is None:
                continue
            frame = self._composite_watermark(frame, wm_img, wm)
        return frame

    # ------------------------------------------------------------------ #
    #  Get watermark bounding rect in frame coordinates                   #
    #  Returns (x, y, w, h) or None for tile/fill modes                   #
    # ------------------------------------------------------------------ #
    def render_watermark_overlay(self, watermarks: List[Watermark]) -> Optional[PILImage.Image]:
        """Render all watermarks onto a transparent canvas for export."""
        if self._frame_pil is None:
            return None
        cw, ch = self._frame_pil.size
        overlay = PILImage.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for wm in watermarks:
            if wm.wm_type == WatermarkType.IMAGE:
                wm_img = self._render_image_watermark(wm, (cw, ch))
            else:
                wm_img = self._render_text_watermark(wm, (cw, ch))
            if wm_img is None:
                continue
            fp = overlay.copy()
            fp = self._composite_watermark(fp, wm_img, wm)
            overlay = fp
        return overlay

    def get_watermark_rect(self, wm: Watermark) -> Optional[Tuple[int, int, int, int]]:
        """Return (x, y, width, height) of a single watermark in frame pixels."""
        if wm.tiling_mode in (TilingMode.TILE, TilingMode.FILL):
            return None
        if self._frame_pil is None:
            return None

        # Render the watermark element to get its size
        if wm.wm_type == WatermarkType.IMAGE:
            elem = self._render_image_watermark(wm, self._frame_pil.size)
        else:
            elem = self._render_text_watermark(wm, self._frame_pil.size)
        if elem is None:
            return None

        iw, ih = elem.size
        cw, ch = self._frame_pil.size
        px, py = self._calc_position(iw, ih, cw, ch, wm)
        return px, py, iw, ih

    # ------------------------------------------------------------------ #
    #  Image watermark                                                     #
    # ------------------------------------------------------------------ #
    def _render_image_watermark(self, wm: Watermark, canvas_size: Tuple[int, int]) -> Optional[PILImage.Image]:
        if not wm.image_path:
            return None
        try:
            img = PILImage.open(wm.image_path).convert("RGBA")
        except Exception:
            return None
        return self._apply_common_transforms(img, wm)

    # ------------------------------------------------------------------ #
    #  Text watermark                                                      #
    # ------------------------------------------------------------------ #
    def _render_text_watermark(self, wm: Watermark, canvas_size: Tuple[int, int]) -> Optional[PILImage.Image]:
        text = wm.text_content or "watermark"
        base_size = max(10, wm.font_size)

        font = None
        if self._chinese_font_path:
            try:
                font = ImageFont.truetype(self._chinese_font_path, base_size)
            except Exception:
                pass
        if font is None:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()

        dummy = PILImage.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0] + 16
        th = bbox[3] - bbox[1] + 16

        txt_img = PILImage.new("RGBA", (tw, th), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((8, 8), text, font=font, fill=wm.font_color + "FF")
        return self._apply_common_transforms(txt_img, wm)

    # ------------------------------------------------------------------ #
    #  Common transforms                                                  #
    # ------------------------------------------------------------------ #
    def _apply_common_transforms(self, img: PILImage.Image, wm: Watermark) -> PILImage.Image:
        img = img.convert("RGBA")
        scale = wm.scale_percent / 100.0
        iw, ih = img.size
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))
        if (new_w, new_h) != (iw, ih):
            img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
        if wm.rotation != 0:
            img = img.rotate(wm.rotation, expand=True, resample=PILImage.Resampling.BICUBIC)
        r, g, b, a = img.split()
        a = a.point(lambda x: int(x * wm.opacity / 100))
        img = PILImage.merge("RGBA", (r, g, b, a))
        if wm.tiling_mode == TilingMode.FILL:
            cw, ch = self._frame_pil.size if self._frame_pil else (1920, 1080)
            img = img.resize((cw, ch), PILImage.Resampling.LANCZOS)
        return img

    # ------------------------------------------------------------------ #
    #  Composite                                                           #
    # ------------------------------------------------------------------ #
    def _composite_watermark(self, frame: PILImage.Image, wm_img: PILImage.Image,
                             wm: Watermark) -> PILImage.Image:
        cw, ch = frame.size
        iw, ih = wm_img.size
        if wm.tiling_mode == TilingMode.TILE:
            fp = frame.convert("RGBA")
            gap = wm.tile_spacing
            for y in range(0, ch, ih + gap):
                for x in range(0, cw, iw + gap):
                    fp.paste(wm_img, (x, y), wm_img)
            return fp
        px, py = self._calc_position(iw, ih, cw, ch, wm)
        fp = frame.convert("RGBA")
        fp.paste(wm_img, (px, py), wm_img)
        return fp

    def _composite_only_wmark(self, frame: PILImage.Image, wm_img: PILImage.Image,
                              wm: Watermark) -> PILImage.Image:
        cw, ch = frame.size
        iw, ih = wm_img.size
        transparent = PILImage.new("RGBA", (cw, ch), (0, 0, 0, 0))
        if wm.tiling_mode == TilingMode.TILE:
            fp = transparent
            gap = wm.tile_spacing
            for y in range(0, ch, ih + gap):
                for x in range(0, cw, iw + gap):
                    fp.paste(wm_img, (x, y), wm_img)
            return fp
        px, py = self._calc_position(iw, ih, cw, ch, wm)
        fp = transparent
        fp.paste(wm_img, (px, py), wm_img)
        return fp

    @staticmethod
    def _calc_position(w: int, h: int, cw: int, ch: int, wm: Watermark) -> Tuple[int, int]:
        if wm.position_preset == PositionPreset.CUSTOM:
            return wm.custom_x, wm.custom_y
        margin = 20
        preset_map = {
            PositionPreset.TOP_LEFT: (margin, margin),
            PositionPreset.TOP_CENTER: ((cw - w) // 2, margin),
            PositionPreset.TOP_RIGHT: (cw - w - margin, margin),
            PositionPreset.CENTER_LEFT: (margin, (ch - h) // 2),
            PositionPreset.CENTER: ((cw - w) // 2, (ch - h) // 2),
            PositionPreset.CENTER_RIGHT: (cw - w - margin, (ch - h) // 2),
            PositionPreset.BOTTOM_LEFT: (margin, ch - h - margin),
            PositionPreset.BOTTOM_CENTER: ((cw - w) // 2, ch - h - margin),
            PositionPreset.BOTTOM_RIGHT: (cw - w - margin, ch - h - margin),
        }
        return preset_map.get(wm.position_preset, (0, 0))

    def export_image(self, watermarks: List[Watermark], output_path: str) -> Tuple[bool, str]:
        if self._frame_pil is None:
            return False, "No source image loaded"
        try:
            result = self.render_preview(watermarks)
            if result is None:
                return False, "Failed to render watermarks"
            result = result.convert("RGB")
            result.save(output_path, quality=95)
            return True, ""
        except Exception as e:
            return False, f"Image export failed: {str(e)}"
