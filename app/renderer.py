import cv2
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
from typing import Optional, Tuple, List
from app.watermark import Watermark, WatermarkType, TilingMode, PositionPreset
import os


def _find_chinese_font() -> str:
    """Find a Chinese-capable TrueType font on Windows."""
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
    # Fallback: try to find any .ttf/.ttc font
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
    """Preview rendering engine — composite watermarks onto video frames"""

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

    def load_frame(self, video_path: Optional[str] = None, time_sec: float = 0.0) -> bool:
        if video_path:
            self.video_path = video_path
        if not self.video_path:
            return False
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return False
        fps = cap.get(cv2.CAP_PROP_FPS)
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
        """Load a static image as the source (instead of a video frame)."""
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

    def is_image_source(self) -> bool:
        return self._is_image_source

    def get_frame_size(self) -> Tuple[int, int]:
        return self.video_width, self.video_height

    def render_preview(self, watermarks: List[Watermark]) -> Optional[PILImage.Image]:
        if self._frame_pil is None:
            return None
        frame = self._frame_pil.copy()
        # if self._is_image_source and frame.mode != "RGBA":
        frame = frame.convert("RGBA")
        print('render preview！')
        for wm in watermarks:
            if wm.wm_type == WatermarkType.IMAGE:
                wm_img = self._render_image_watermark(wm, frame.size)
            else:
                wm_img = self._render_text_watermark(wm, frame.size)
            if wm_img is None:
                continue
            frame = self._composite_watermark(frame, wm_img, wm)
            self.ori_wm_composite = self._composite_only_wmark(frame, wm_img, wm)
        return frame

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
    #  Text watermark — render text at native size then scale uniformly    #
    # ------------------------------------------------------------------ #
    def _render_text_watermark(self, wm: Watermark, canvas_size: Tuple[int, int]) -> Optional[PILImage.Image]:
        text = wm.text_content or "watermark"
        base_size = max(10, wm.font_size)

        # Use Chinese font if available, otherwise fallback
        font = None
        if self._chinese_font_path:
            try:
                font = ImageFont.truetype(self._chinese_font_path, base_size)
            except Exception:
                pass
        if font is None:
            try:
                if wm.font_path:
                    font = ImageFont.truetype(wm.font_path, base_size)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()

        # Measure text
        dummy = PILImage.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 8
        tw += padding * 2
        th += padding * 2

        # Render text onto RGBA canvas
        txt_img = PILImage.new("RGBA", (tw, th), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((padding, padding), text, font=font, fill=wm.font_color + "FF")

        # Uniformly scale using common transforms (scale is applied here only ONCE)
        return self._apply_common_transforms(txt_img, wm)

    # ------------------------------------------------------------------ #
    #  Common: scale + rotate + opacity (applied exactly once)            #
    # ------------------------------------------------------------------ #
    def _apply_common_transforms(self, img: PILImage.Image, wm: Watermark) -> PILImage.Image:
        img = img.convert("RGBA")
        scale = wm.scale_percent / 100.0

        # Scale
        iw, ih = img.size
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))
        if (new_w, new_h) != (iw, ih):
            img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)

        # Rotate
        if wm.rotation != 0:
            img = img.rotate(wm.rotation, expand=True, resample=PILImage.Resampling.BICUBIC)

        # Opacity
        r, g, b, a = img.split()
        a = a.point(lambda x: int(x * wm.opacity / 100))
        img = PILImage.merge("RGBA", (r, g, b, a))

        # Fill mode
        if wm.tiling_mode == TilingMode.FILL:
            cw, ch = self._frame_pil.size if self._frame_pil else (1920, 1080)
            img = img.resize((cw, ch), PILImage.Resampling.LANCZOS)

        return img

    # ------------------------------------------------------------------ #
    #  Composite onto frame                                                #
    # ------------------------------------------------------------------ #
    def _composite_watermark(self, frame: PILImage.Image, wm_img: PILImage.Image,
                             wm: Watermark) -> PILImage.Image:
        cw, ch = frame.size
        iw, ih = wm_img.size

        if wm.tiling_mode == TilingMode.TILE:
            frame_pil = frame.convert("RGBA")
            for y in range(0, ch, ih):
                for x in range(0, cw, iw):
                    frame_pil.paste(wm_img, (x, y), wm_img)
            return frame_pil

        px, py = self._calc_position(iw, ih, cw, ch, wm)
        frame_pil = frame.convert("RGBA")
        frame_pil.paste(wm_img, (px, py), wm_img)
        return frame_pil
    
    def _composite_only_wmark(self, frame: PILImage.Image, wm_img: PILImage.Image,
                             wm: Watermark) -> PILImage.Image:
        cw, ch = frame.size
        iw, ih = wm_img.size
        transparent_img = PILImage.new("RGBA", (cw, ch), (0, 0, 0, 0))

        if wm.tiling_mode == TilingMode.TILE:
            frame_pil = transparent_img
            for y in range(0, ch, ih):
                for x in range(0, cw, iw):
                    frame_pil.paste(wm_img, (x, y), wm_img)
            return frame_pil

        px, py = self._calc_position(iw, ih, cw, ch, wm)
        frame_pil = transparent_img
        frame_pil.paste(wm_img, (px, py), wm_img)
        return frame_pil

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

    # ------------------------------------------------------------------ #
    #  Export watermarked image                                           #
    # ------------------------------------------------------------------ #
    def export_image(self, watermarks: List[Watermark], output_path: str) -> Tuple[bool, str]:
        """Composite watermarks onto the source image and save to output_path."""
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
