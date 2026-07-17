from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFileDialog, QSlider
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPointF
from PySide6.QtGui import (
    QPixmap, QImage, QFont, QPainter, QPen, QBrush, QColor,
    QDragEnterEvent, QDropEvent, QDragLeaveEvent, QMouseEvent
)
import os as _os
from PIL import Image as PILImage
from watermark.app.renderer import WatermarkRenderer
from watermark.app.watermark import Watermark, PositionPreset

HANDLE_SIZE = 12
HANDLE_COLOR = QColor("#5dade2")
HANDLE_FILL = QColor("#1a1a2e")
BORDER_PEN = QPen(QColor("#5dade2"), 1, Qt.DashLine)


class PreviewCanvas(QWidget):
    file_dropped = Signal(str)
    watermark_moved = Signal(int, int)
    watermark_scaled = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setMinimumSize(480, 360)
        self.setFocusPolicy(Qt.StrongFocus)
        self._pixmap = QPixmap()
        self._empty_text = "Drop video or image here"
        self._is_empty = True
        self._selected_wm = None
        self._wm_rect_frame = None
        self._dragging = False
        self._drag_mode = ""
        self._drag_start_frame_pt = (0.0, 0.0)
        self._drag_start_scale = 100
        self._drag_start_rect = (0, 0, 0, 0)
        self._drag_hovering = False
        self._mouse_hovering = False

    # -- public api ------------------------------------------------------------
    def set_pixmap(self, pm):
        self._pixmap = pm
        self._is_empty = False
        self.update()

    def clear_pixmap(self):
        self._pixmap = QPixmap()
        self._is_empty = True
        self._selected_wm = None
        self._wm_rect_frame = None
        self.update()

    def set_selected_watermark(self, wm, rect_frame):
        if wm and rect_frame and wm.position_preset == PositionPreset.CUSTOM:
            self._selected_wm = wm
            self._wm_rect_frame = rect_frame
        else:
            self._selected_wm = None
            self._wm_rect_frame = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    # -- coordinate helpers ----------------------------------------------------
    def _display_rect(self):
        if self._pixmap.isNull():
            return QRect()
        pm = self._pixmap
        ws = self.size()
        scaled = pm.scaled(ws, Qt.KeepAspectRatio, Qt.SmoothTransformation).size()
        x = (ws.width() - scaled.width()) // 2
        y = (ws.height() - scaled.height()) // 2
        return QRect(x, y, scaled.width(), scaled.height())

    def _frame_size(self):
        p = self.parent()
        if p and hasattr(p, "renderer"):
            return (p.renderer.video_width, p.renderer.video_height)
        return (640, 480)

    def _frame_to_widget(self, fx, fy):
        dr = self._display_rect()
        vw, vh = self._frame_size()
        if dr.width() == 0 or vw == 0:
            return QPointF(fx, fy)
        sx = dr.width() / vw
        sy = dr.height() / vh
        return QPointF(dr.x() + fx * sx, dr.y() + fy * sy)

    def _widget_to_frame(self, wx, wy):
        dr = self._display_rect()
        vw, vh = self._frame_size()
        if dr.width() == 0 or vw == 0:
            return (wx, wy)
        sx = vw / dr.width()
        sy = vh / dr.height()
        fx = (wx - dr.x()) * sx
        fy = (wy - dr.y()) * sy
        return (fx, fy)

    # -- handle geometry -------------------------------------------------------
    def _handle_rects(self):
        if self._wm_rect_frame is None or self._selected_wm is None:
            return {}
        fx, fy, fw, fh = self._wm_rect_frame
        tl = self._frame_to_widget(fx, fy)
        br = self._frame_to_widget(fx + fw, fy + fh)
        h2 = HANDLE_SIZE / 2
        pts = {
            "tl": tl,
            "tr": QPointF(br.x(), tl.y()),
            "bl": QPointF(tl.x(), br.y()),
            "br": br,
        }
        return {n: QRectF(p.x() - h2, p.y() - h2, HANDLE_SIZE, HANDLE_SIZE) for n, p in pts.items()}

    def _body_rect(self):
        if self._wm_rect_frame is None:
            return QRectF()
        fx, fy, fw, fh = self._wm_rect_frame
        tl = self._frame_to_widget(fx, fy)
        br = self._frame_to_widget(fx + fw, fy + fh)
        return QRectF(tl, br)

    def _hit_test(self, pos):
        for name, rect in self._handle_rects().items():
            if rect.contains(pos):
                return name
        if self._body_rect().contains(pos):
            return "move"
        return ""

    # -- paint -----------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        if self._is_empty or self._pixmap.isNull():
            if self._mouse_hovering or self._drag_hovering:
                self._paint_drag_hint(painter, overlay=self._drag_hovering)
            else:
                painter.setPen(QColor("#666"))
                f = self.font()
                f.setPointSize(12)
                painter.setFont(f)
                painter.drawText(self.rect(), Qt.AlignCenter, self._empty_text)
            painter.end()
            return

        dr = self._display_rect()
        painter.drawPixmap(dr, self._pixmap, self._pixmap.rect())

        if self._mouse_hovering or self._drag_hovering:
            self._paint_drag_hint(painter, overlay=self._drag_hovering)

        if self._selected_wm and self._wm_rect_frame:
            body = self._body_rect()
            painter.setPen(BORDER_PEN)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(body)
            painter.setPen(QPen(HANDLE_COLOR, 1))
            painter.setBrush(QBrush(HANDLE_FILL))
            for r in self._handle_rects().values():
                painter.drawRect(r)

        painter.end()

    def _paint_drag_hint(self, painter, overlay=False):
        if overlay:
            clr = QColor("#5dade2")
            clr.setAlpha(30)
            painter.fillRect(self.rect(), clr)
        pen = QPen(QColor("#5dade2"), 2, Qt.DashLine)
        painter.setPen(pen)
        margin = 8
        painter.drawRoundedRect(self.rect().adjusted(margin, margin, -margin, -margin), 8, 8)
        f = self.font()
        f.setPointSize(14)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor("#7ebef2"))
        painter.drawText(self.rect(), Qt.AlignCenter, "拖拽文件到此处释放")

    # -- mouse -----------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self._selected_wm or not self._wm_rect_frame:
            super().mousePressEvent(event)
            return
        pos = event.position()
        mode = self._hit_test(QPointF(pos))
        if not mode:
            super().mousePressEvent(event)
            return

        self._dragging = True
        self._drag_mode = mode
        self._drag_start_frame_pt = self._widget_to_frame(pos.x(), pos.y())
        self._drag_start_scale = self._selected_wm.scale_percent
        self._drag_start_rect = self._wm_rect_frame
        event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._dragging:
            fx, fy = self._widget_to_frame(pos.x(), pos.y())
            sfx, sfy = self._drag_start_frame_pt
            dx, dy = fx - sfx, fy - sfy

            if self._drag_mode == "move":
                ox, oy, _, _ = self._drag_start_rect
                nx = max(0, int(ox + dx))
                ny = max(0, int(oy + dy))
                self._selected_wm.custom_x = nx
                self._selected_wm.custom_y = ny
                self.watermark_moved.emit(nx, ny)

            elif self._drag_mode in ("tl", "tr", "bl", "br"):
                ox, oy, ow, oh = self._drag_start_rect
                mode = self._drag_mode
                ax, ay = {
                    "tl": (ox + ow, oy + oh),
                    "tr": (ox, oy + oh),
                    "bl": (ox + ow, oy),
                    "br": (ox, oy),
                }[mode]
                nw = abs(fx - ax)
                if ow > 0 and nw > 5:
                    ns = max(5, min(500, int(nw / ow * self._drag_start_scale)))
                    self._selected_wm.scale_percent = ns
                    self.watermark_scaled.emit(ns)

            self._update_wm_rect()
            self.update()
            event.accept()
            return

        if self._selected_wm and self._wm_rect_frame:
            mode = self._hit_test(QPointF(pos))
            cursor_map = {
                "tl": Qt.SizeFDiagCursor, "tr": Qt.SizeBDiagCursor,
                "bl": Qt.SizeBDiagCursor, "br": Qt.SizeFDiagCursor,
                "move": Qt.SizeAllCursor,
            }
            self.setCursor(cursor_map.get(mode, Qt.ArrowCursor))

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._drag_mode = ""
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _update_wm_rect(self):
        if self._selected_wm is None:
            self._wm_rect_frame = None
            return
        p = self.parent()
        if p and hasattr(p, "renderer"):
            self._wm_rect_frame = p.renderer.get_watermark_rect(self._selected_wm)

    # -- mouse enter/leave -----------------------------------------------------
    def enterEvent(self, event):
        self._mouse_hovering = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._mouse_hovering = False
        self.update()
        super().leaveEvent(event)

    # -- drag-drop -------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._drag_hovering = True
            self.update()
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return
        self._drag_hovering = False
        urls = event.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())

    def dragLeaveEvent(self, event):
        self._drag_hovering = False
        self.update()


class PreviewPanel(QWidget):
    video_loaded = Signal(str)
    frame_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = WatermarkRenderer()
        self.current_pixmap = QPixmap()
        self._has_content = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid #3a3a3a;")
        tl = QHBoxLayout(title_bar)
        tl.setContentsMargins(8, 6, 8, 6)
        title = QLabel("Preview")
        title.setStyleSheet("color: #8ab4d6; font-weight: 600; font-size: 12px; background: transparent;")
        tl.addWidget(title)
        tl.addStretch()

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet(
            "QPushButton { background: #3a3a3a; border: 1px solid #4d4d4d;"
            "border-radius: 2px; padding: 4px 14px; color: #d4d4d4; font-size: 11px; }"
            "QPushButton:hover { background: #484848; border-color: #5dade2; }"
        )
        self.browse_btn.clicked.connect(self._browse_file)
        tl.addWidget(self.browse_btn)
        layout.addWidget(title_bar)

        self.canvas = PreviewCanvas()
        self.canvas.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self.canvas, 1)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)
        self.frame_slider.setVisible(False)
        self.frame_slider.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #3a3a3a; border-radius: 2px; } QSlider::handle:horizontal { background: #5dade2; width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; } QSlider::handle:horizontal:hover { background: #7ebef2; } QSlider::sub-page:horizontal { background: #4a7fa0; border-radius: 2px; }")
        self.frame_slider.valueChanged.connect(self._on_slider_seek)
        layout.addWidget(self.frame_slider)

        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: #888; padding: 3px 8px; font-size: 11px; background: #2a2a2a;"
            "border-top: 1px solid #3a3a3a;"
        )
        self.info_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.info_label)

    def _on_slider_seek(self, frame_idx: int):
        if not self._has_content or self.renderer.is_image_source():
            return
        fps = self.renderer.get_video_fps()
        time_sec = frame_idx / fps if fps > 0 else 0.0
        self.renderer.load_frame(time_sec=time_sec)
        self.frame_changed.emit(frame_idx)

    def _on_file_dropped(self, path):
        ext = _os.path.splitext(path)[1].lower()
        img_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
        if ext in img_exts:
            self.load_image(path)
        else:
            self.load_video(path)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video or Image File", "",
            "Media files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.png *.jpg *.jpeg *.bmp *.tiff *.webp);;"
            "Video files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;"
            "Image files (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All files (*.*)"
        )
        if path:
            ext = _os.path.splitext(path)[1].lower()
            img_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
            if ext in img_exts:
                self.load_image(path)
            else:
                self.load_video(path)

    def load_video(self, path):
        if self.renderer.load_frame(path):
            self._has_content = True
            w, h = self.renderer.get_frame_size()
            total = self.renderer.get_total_frames()
            self.info_label.setText(f"Video  |  {w}x{h}  |  {(w*h)//1000}K pixels  |  {total} frames")
            self.frame_slider.setMaximum(max(0, total - 1))
            self.frame_slider.setValue(0)
            self.frame_slider.setVisible(True)
            self.video_loaded.emit(path)

    def load_image(self, path):
        if self.renderer.load_image(path):
            self._has_content = True
            w, h = self.renderer.get_frame_size()
            self.info_label.setText(f"Image  |  {w}x{h}  |  {(w*h)//1000}K pixels")
            self.frame_slider.setMaximum(0)
            self.frame_slider.setValue(0)
            self.frame_slider.setVisible(False)
            self.video_loaded.emit(path)

    def set_selected_watermark(self, wm):
        if wm and self._has_content:
            rect = self.renderer.get_watermark_rect(wm)
            self.canvas.set_selected_watermark(wm, rect)
        else:
            self.canvas.set_selected_watermark(None, None)

    def update_preview(self, watermarks):
        pil_img = self.renderer.render_preview(watermarks)
        if pil_img is None:
            return False
        ws = self.canvas.size()
        if ws.width() > 0 and ws.height() > 0:
            pil_img.thumbnail((ws.width(), ws.height()), PILImage.Resampling.LANCZOS)
        qimage = QImage(
            pil_img.tobytes("raw", "RGBA"),
            pil_img.width, pil_img.height,
            QImage.Format.Format_RGBA8888,
        )
        pm = QPixmap.fromImage(qimage)
        self.current_pixmap = pm
        self.canvas.set_pixmap(pm)
        return True

