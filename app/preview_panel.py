from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QFont, QDragEnterEvent, QDropEvent, QDragLeaveEvent
import os
from PIL import Image as PILImage
from app.renderer import WatermarkRenderer


class DropLabel(QLabel):
    """QLabel that accepts drag-and-drop of files."""
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            return
        urls = event.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())


class PreviewPanel(QWidget):
    video_loaded = Signal(str)

    DROP_HINT = "Drag & drop video or image here\n\nSupported: mp4, avi, mov, mkv, wmv, flv, webm, png, jpg, jpeg, bmp, tiff, webp"
    DRAG_OVER_TEXT = "Release to load file"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = WatermarkRenderer()
        self.current_pixmap: QPixmap = QPixmap()
        self._has_content = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid #3a3a3a;")
        tl = QHBoxLayout(title_bar)
        tl.setContentsMargins(8, 6, 8, 6)
        title = QLabel("Preview")
        title.setStyleSheet("color: #8ab4d6; font-weight: 600; font-size: 12px; background: transparent;")
        tl.addWidget(title)
        tl.addStretch()

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4d4d4d;
                border-radius: 2px;
                padding: 4px 14px;
                color: #d4d4d4;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #484848;
                border-color: #5dade2;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        tl.addWidget(self.browse_btn)

        layout.addWidget(title_bar)

        # drop zone preview label
        self.preview_label = DropLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(480, 360)
        self.preview_label.file_dropped.connect(self._on_file_dropped)
        self._apply_empty_style()

        # info bar
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: #888; padding: 3px 8px; font-size: 11px; background: #2a2a2a;"
            "border-top: 1px solid #3a3a3a;"
        )
        self.info_label.setFont(QFont("Segoe UI", 9))

        layout.addWidget(title_bar)
        layout.addWidget(self.preview_label, 1)
        layout.addWidget(self.info_label)

    # --- Styles ---

    def _apply_empty_style(self):
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px dashed #4a4a4a;
                border-radius: 8px;
                color: #666;
                font-size: 14px;
                padding: 20px;
            }
            QLabel:hover {
                border-color: #5dade2;
                color: #888;
            }
        """)
        if not self._has_content:
            self.preview_label.setText(self.DROP_HINT)

    def _apply_dragover_style(self):
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1e2a30;
                border: 2px dashed #5dade2;
                border-radius: 8px;
                color: #8ab4d6;
                font-size: 15px;
                padding: 20px;
            }
        """)
        if not self._has_content:
            self.preview_label.setText(self.DRAG_OVER_TEXT)

    def _apply_loaded_style(self):
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #3e3e3e;
                border-radius: 2px;
            }
        """)

    # --- Drag visual feedback ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._apply_dragover_style()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        if not self._has_content:
            self._apply_empty_style()
        else:
            self._apply_loaded_style()

    # --- File drop handling ---

    def _on_file_dropped(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        img_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        if ext in img_exts:
            self.load_image(path)
        else:
            self.load_video(path)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video or Image File", "",
            "Media files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.png *.jpg *.jpeg *.bmp *.tiff *.webp);;Video files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;Image files (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All files (*.*)"
        )
        if path:
            ext = os.path.splitext(path)[1].lower()
            img_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
            if ext in img_exts:
                self.load_image(path)
            else:
                self.load_video(path)

    def load_video(self, path: str):
        if self.renderer.load_frame(path):
            self._has_content = True
            self._apply_loaded_style()
            w, h = self.renderer.get_frame_size()
            self.info_label.setText(f"Video  |  {w}x{h}  |  {(w*h)//1000}K pixels")
            self.video_loaded.emit(path)
        else:
            raise ImportError(f'{path}导入出了点问题')

    def load_image(self, path: str):
        if self.renderer.load_image(path):
            self._has_content = True
            self._apply_loaded_style()
            w, h = self.renderer.get_frame_size()
            self.info_label.setText(f"Image  |  {w}x{h}  |  {(w*h)//1000}K pixels")
            self.video_loaded.emit(path)

    # --- Preview update ---

    def update_preview(self, watermarks) -> bool:
        pil_img = self.renderer.render_preview(watermarks)
        if pil_img is None:
            print('没有图！')
            return False

        label_size = self.preview_label.size()
        if label_size.width() > 0 and label_size.height() > 0:
            pil_img.thumbnail(
                (label_size.width(), label_size.height()),
                PILImage.Resampling.LANCZOS
            )
        print(pil_img)
        qimage = QImage(
            pil_img.tobytes("raw", "RGBA"),
            pil_img.width, pil_img.height,
            QImage.Format.Format_RGBA8888
        )
        self.current_pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(self.current_pixmap)
        return True
