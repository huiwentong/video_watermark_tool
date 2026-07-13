import subprocess
import os
import tempfile
from typing import List, Tuple, Optional
from PIL import Image as PILImage, ImageDraw, ImageFont
from app.watermark import Watermark, WatermarkType, TilingMode, PositionPreset


def _find_chinese_font() -> str:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/yahei.ttf",
        "C:/Windows/Fonts/Deng.ttf",
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


def _escape_filter(value: str) -> str:
    result = ""
    for ch in value:
        if ch == "\\":
            result += "\\\\\\\\"
        elif ch in ":,\\[\\]%'":
            result += "\\\\" + ch
        else:
            result += ch
    return result


def _filter_path(path: str) -> str:
    fp = path.replace("\\", "/")
    fp = fp.replace(":", "\\\\:")
    return fp


class WatermarkExporter:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._chinese_font_path = _find_chinese_font()
        self._temp_files: List[str] = []

    def _cleanup(self):
        for p in self._temp_files:
            try:
                if os.path.isfile(p):
                    os.unlink(p)
            except Exception:
                pass
        self._temp_files.clear()

    def _new_temp_file(self, suffix: str) -> str:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        f.close()
        self._temp_files.append(f.name)
        return f.name

    # ------------------------------------------------------------------ #
    #  Render single watermark element (text or image)                    #
    #  Returns a PIL RGBA image at the final size (scaled, rotated,       #
    #  opacity applied), ready for compositing.                           #
    # ------------------------------------------------------------------ #
    def _render_watermark_element(self, wm: Watermark) -> Optional[PILImage.Image]:
        """Render a single watermark instance to a PIL RGBA image
        (scale + rotation + opacity applied, but NOT tiled/filled)."""
        if wm.wm_type == WatermarkType.TEXT:
            return self._render_text_element(wm)
        elif wm.wm_type == WatermarkType.IMAGE:
            return self._render_image_element(wm)
        return None

    def _render_text_element(self, wm: Watermark) -> Optional[PILImage.Image]:
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
        return txt_img

    def _render_image_element(self, wm: Watermark) -> Optional[PILImage.Image]:
        if not os.path.isfile(wm.image_path):
            return None
        try:
            return PILImage.open(wm.image_path).convert("RGBA")
        except Exception:
            return None

    def _apply_common_transforms(self, img: PILImage.Image, wm: Watermark) -> PILImage.Image:
        """Apply scale, rotation, opacity to a watermark image."""
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
        return img

    def _render_tiled_image(self, wm: Watermark, canvas_w: int, canvas_h: int) -> Optional[str]:
        """Pre-render a tiled watermark covering the full canvas, save as PNG.
        Returns the path to the temp PNG file."""
        elem = self._render_watermark_element(wm)
        if elem is None:
            return None
        elem = self._apply_common_transforms(elem, wm)

        # Tile it across canvas
        iw, ih = elem.size
        if iw == 0 or ih == 0:
            return None

        canvas = PILImage.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        for y in range(0, canvas_h, ih):
            for x in range(0, canvas_w, iw):
                canvas.paste(elem, (x, y), elem)

        out = self._new_temp_file(".png")
        canvas.save(out, "PNG")
        return out

    def _render_fill_image(self, wm: Watermark, canvas_w: int, canvas_h: int) -> Optional[str]:
        """Render watermark stretched to fill the canvas, save as PNG."""
        elem = self._render_watermark_element(wm)
        if elem is None:
            return None
        elem = self._apply_common_transforms(elem, wm)
        elem = elem.resize((canvas_w, canvas_h), PILImage.Resampling.LANCZOS)
        out = self._new_temp_file(".png")
        elem.save(out, "PNG")
        return out

    # ------------------------------------------------------------------ #
    #  Pre-process: convert complex watermarks to simple image overlays   #
    #  (rotated text, tiled text, tiled image, filled text)               #
    # ------------------------------------------------------------------ #
    def _prepare_watermarks(self, watermarks: List[Watermark],
                            vw: int, vh: int) -> Tuple[List, List[str]]:
        """Return (processed_wms, extra_png_paths) where complex watermarks
        are replaced by simple image overlays referencing pre-rendered PNGs."""
        result: List[Watermark] = []
        extra: List[str] = []

        for wm in watermarks:
            needs_render = False
            png = None

            if wm.wm_type == WatermarkType.TEXT:
                if wm.rotation != 0 or wm.tiling_mode == TilingMode.TILE or wm.tiling_mode == TilingMode.FILL:
                    needs_render = True

            elif wm.wm_type == WatermarkType.IMAGE:
                if wm.tiling_mode == TilingMode.TILE or wm.tiling_mode == TilingMode.FILL:
                    needs_render = True

            if needs_render:
                if wm.tiling_mode == TilingMode.TILE:
                    png = self._render_tiled_image(wm, vw, vh)
                    new_tiling = TilingMode.NONE
                    new_x, new_y = 0, 0
                    new_pos = PositionPreset.TOP_LEFT
                elif wm.tiling_mode == TilingMode.FILL:
                    png = self._render_fill_image(wm, vw, vh)
                    new_tiling = TilingMode.NONE
                    new_x, new_y = 0, 0
                    new_pos = PositionPreset.TOP_LEFT
                else:
                    # rotated single text ¡ú render with transforms, overlay at position
                    elem = self._render_watermark_element(wm)
                    if elem:
                        elem = self._apply_common_transforms(elem, wm)
                        png = self._new_temp_file(".png")
                        elem.save(png, "PNG")
                    new_tiling = TilingMode.NONE
                    new_x, new_y = wm.custom_x, wm.custom_y
                    new_pos = wm.position_preset

                if png:
                    extra.append(png)
                    result.append(Watermark(
                        wm_type=WatermarkType.IMAGE,
                        image_path=png,
                        opacity=100,
                        scale_percent=100,
                        rotation=0,
                        tiling_mode=new_tiling,
                        position_preset=new_pos,
                        custom_x=new_x,
                        custom_y=new_y,
                    ))
                else:
                    # fallback: keep original if rendering failed
                    result.append(wm)
            else:
                result.append(wm)

        return result, extra

    # ------------------------------------------------------------------ #
    #  Build filter graph                                                  #
    # ------------------------------------------------------------------ #
    def _build_filter(self, watermarks: List[Watermark],
                      video_w: int, video_h: int) -> Optional[str]:
        filters = []
        current_label = "[0:v]"
        label_idx = 1

        for wm in watermarks:
            if wm.wm_type == WatermarkType.IMAGE:
                stream_idx = self._img_stream_counter
                self._img_stream_counter += 1
                result = self._build_image_filter(wm, video_w, video_h,
                                                  current_label, stream_idx, label_idx)
                if result:
                    f_text, new_label, label_idx = result
                    filters.append(f_text)
                    current_label = new_label
                    label_idx += 1
            elif wm.wm_type == WatermarkType.TEXT:
                result = self._build_text_filter(wm, video_w, video_h,
                                                 current_label, label_idx)
                if result:
                    f_text, new_label, label_idx = result
                    filters.append(f_text)
                    current_label = new_label
                    label_idx += 1

        if filters:
            return ";\n".join(filters) + f";{current_label}format=yuv420p[out]"
        return None

    # ------------------------------------------------------------------ #
    #  TEXT watermark (drawtext) ¡ª only for no-rotation single text       #
    # ------------------------------------------------------------------ #
    def _build_text_filter(self, wm: Watermark, vw: int, vh: int,
                           current_label: str, label_idx: int):
        fontsize = max(10, int(wm.font_size * wm.scale_percent / 100))
        opacity = wm.opacity / 100.0
        color = wm.font_color.lstrip("#")
        if len(color) != 6:
            color = "FFFFFF"
        fontcolor = f"{color}@{opacity:.2f}"
        escaped_text = _escape_filter(wm.text_content or "watermark")

        fontfile_arg = ""
        if self._chinese_font_path:
            ff_path = _filter_path(self._chinese_font_path)
            fontfile_arg = f":fontfile={ff_path}"

        px, py = self._calc_pos(vw, vh, wm)
        dt = (
            f"drawtext=text={escaped_text}:fontsize={fontsize}"
            f":fontcolor={fontcolor}{fontfile_arg}"
            f":x={px}:y={py}"
        )
        return (f"{current_label}{dt}[txt{label_idx}]",
                f"[txt{label_idx}]", label_idx + 1)

    # ------------------------------------------------------------------ #
    #  IMAGE watermark (overlay)                                           #
    # ------------------------------------------------------------------ #
    def _build_image_filter(self, wm: Watermark, vw: int, vh: int,
                            current_label: str, stream_idx: int, label_idx: int):
        if not os.path.isfile(wm.image_path):
            return None

        img_path = _filter_path(wm.image_path)
        scale_pct = wm.scale_percent / 100.0
        ov_label = f"[ov{label_idx}]"
        out_label = f"[tmp{label_idx}]"
        wm_opacity = wm.opacity / 100.0
        stream_ref = f"[{stream_idx}:v]"

        chain = f"scale=iw*{scale_pct}:ih*{scale_pct}"
        if wm.rotation != 0:
            angle_rad = -wm.rotation * 3.14159 / 180.0
            chain += f",rotate={angle_rad:.4f}:ow=rotw({angle_rad:.4f}):oh=roth({angle_rad:.4f}):c=none"

        chain += f",format=rgba,colorchannelmixer=aa={wm_opacity}"
        px, py = self._calc_pixel_pos(vw, vh, wm, wm.image_path)

        ov = (
            f"{stream_ref}{chain}{ov_label};"
            f"{current_label}{ov_label}overlay={px}:{py}:format=auto{out_label}"
        )
        return (ov, out_label, label_idx + 1)

    # ------------------------------------------------------------------ #
    #  Position helpers                                                    #
    # ------------------------------------------------------------------ #
    def _calc_pos(self, vw: int, vh: int, wm: Watermark) -> tuple:
        margin = 20
        if wm.position_preset == PositionPreset.CUSTOM:
            return str(wm.custom_x), str(wm.custom_y)
        iw, ih = self._estimate_text_size(wm)
        return self._resolve_preset(vw, vh, iw, ih, wm.position_preset, margin)

    def _calc_pixel_pos(self, vw: int, vh: int, wm: Watermark, img_path: str) -> tuple:
        margin = 20
        if wm.position_preset == PositionPreset.CUSTOM:
            return str(wm.custom_x), str(wm.custom_y)
        try:
            with PILImage.open(img_path) as img:
                iw, ih = img.size
                scale = wm.scale_percent / 100.0
                iw, ih = int(iw * scale), int(ih * scale)
        except Exception:
            iw, ih = 100, 100
        return self._resolve_preset(vw, vh, iw, ih, wm.position_preset, margin)

    @staticmethod
    def _estimate_text_size(wm: Watermark) -> tuple:
        fontsize = max(10, int(wm.font_size * wm.scale_percent / 100))
        char_w = fontsize * 0.6
        iw = int(char_w * len(wm.text_content or "W"))
        ih = fontsize + 10
        return iw, ih

    @staticmethod
    def _resolve_preset(vw: int, vh: int, iw: int, ih: int,
                        preset: PositionPreset, margin: int) -> tuple:
        preset_map = {
            PositionPreset.TOP_LEFT: (margin, margin),
            PositionPreset.TOP_CENTER: ((vw - iw) // 2, margin),
            PositionPreset.TOP_RIGHT: (vw - iw - margin, margin),
            PositionPreset.CENTER_LEFT: (margin, (vh - ih) // 2),
            PositionPreset.CENTER: ((vw - iw) // 2, (vh - ih) // 2),
            PositionPreset.CENTER_RIGHT: (vw - iw - margin, (vh - ih) // 2),
            PositionPreset.BOTTOM_LEFT: (margin, vh - ih - margin),
            PositionPreset.BOTTOM_CENTER: ((vw - iw) // 2, vh - ih - margin),
            PositionPreset.BOTTOM_RIGHT: (vw - iw - margin, vh - ih - margin),
        }
        px, py = preset_map.get(preset, (0, 0))
        return str(max(0, px)), str(max(0, py))

    # ------------------------------------------------------------------ #
    #  Export                                                              #
    # ------------------------------------------------------------------ #
    def export(self, input_path: str, output_path: str,
               watermarks: List[Watermark], video_size=None,
               on_progress=None) -> tuple:
        self._cleanup()

        if video_size is None:
            import cv2
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False, "Cannot open video file"
            vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            vw, vh = video_size

        # Pre-process: tile/fill/rotated watermarks ¡ú pre-rendered PNGs
        processed, _ = self._prepare_watermarks(watermarks, vw, vh)

        # Build filter
        self._img_stream_counter = 1
        filter_complex = self._build_filter(processed, vw, vh)
        if filter_complex is None:
            self._cleanup()
            return False, "No watermark filters generated (check image paths)"

        # Build ffmpeg command
        cmd = [self.ffmpeg_path, "-y", "-i", input_path]
        for wm in processed:
            if wm.wm_type == WatermarkType.IMAGE and os.path.isfile(wm.image_path):
                cmd.extend(["-i", wm.image_path])

        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", "[out]"])
        cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23"])
        cmd.extend([output_path])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace"
            )
            stdout_data, stderr_data = process.communicate(timeout=3600)
            process.wait()

            if process.returncode != 0:
                err = (stderr_data or stdout_data or "").strip()
                lines = err.split("\n")
                error_lines = [l for l in lines
                               if any(k in l.lower() for k in ("error", "invalid",
                                                                "unable", "failed"))]
                if not error_lines:
                    error_lines = lines[-5:] if len(lines) > 5 else lines
                err_msg = " | ".join(error_lines[-5:])
                if not err_msg:
                    err_msg = err[-300:]
                return False, f"ffmpeg error (code {process.returncode}): {err_msg}"

            self._cleanup()
            return True, ""
        except FileNotFoundError:
            self._cleanup()
            return False, f"ffmpeg not found at '{self.ffmpeg_path}'"
        except subprocess.TimeoutExpired:
            process.kill()
            self._cleanup()
            return False, "ffmpeg timed out (video too large?)"
        except Exception as e:
            self._cleanup()
            return False, f"Export exception: {str(e)}"
