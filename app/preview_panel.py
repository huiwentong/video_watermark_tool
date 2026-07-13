from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QFont
from PIL import Image as PILImage
from app.renderer import WatermarkRenderer


class PreviewPanel(QWidget):
    video_loaded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = WatermarkRenderer()
        self.current_pixmap: QPixmap = QPixmap()
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

        # file row
        file_row = QWidget()
        file_row.setStyleSheet("background: #2a2a2a;")
        frl = QHBoxLayout(file_row)
        frl.setContentsMargins(8, 4, 8, 6)
        frl.setSpacing(6)

        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select a video file...")
        self.video_path_edit.setReadOnly(True)
        self.video_path_edit.setStyleSheet(
            "background: #3c3c3c; border: 1px solid #4d4d4d; border-radius: 2px; "
            "padding: 5px 8px; color: #b8b8b8; font-size: 11px;"
        )

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet(
            "QPushButton { background: #3a3a3a; border: 1px solid #4d4d4d; "
            "border-radius: 2px; padding: 5px 14px; color: #d4d4d4; font-size: 11px; }"
            "QPushButton:hover { background: #484848; border-color: #5dade2; }"
        )
        browse_btn.clicked.connect(self._browse_video)

        frl.addWidget(self.video_path_edit, 1)
        frl.addWidget(browse_btn)

        # preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(480, 360)
        self.preview_label.setStyleSheet(
            "QLabel { background-color: #1a1a1a; border: 1px solid #3e3e3e; "
            "border-radius: 2px; color: #666; font-size: 13px; }"
        )
        self.preview_label.setText("Select a video file\nClick \u2018Browse\u2019 to load")

        # info bar
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: #888; padding: 3px 8px; font-size: 11px; background: #2a2a2a;"
            "border-top: 1px solid #3a3a3a;"
        )
        self.info_label.setFont(QFont("Segoe UI", 9))

        layout.addWidget(title_bar)
        layout.addWidget(file_row)
        layout.addWidget(self.preview_label, 1)
        layout.addWidget(self.info_label)

    def _browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;All files (*.*)"
        )
        if path:
            self.load_video(path)

    def load_video(self, path: str):
        self.video_path_edit.setText(path)
        if self.renderer.load_frame(path):
            w, h = self.renderer.get_frame_size()
            self.info_label.setText(f"Video  |  {w}\u00d7{h}  |  {(w*h)//1000}K pixels")
            self.video_loaded.emit(path)

    def update_preview(self, watermarks) -> bool:
        pil_img = self.renderer.render_preview(watermarks)
        if pil_img is None:
            return False

        label_size = self.preview_label.size()
        if label_size.width() > 0 and label_size.height() > 0:
            pil_img.thumbnail(
                (label_size.width(), label_size.height()),
                PILImage.Resampling.LANCZOS
            )

        qimage = QImage(
            pil_img.tobytes("raw", "RGBA"),
            pil_img.width, pil_img.height,
            QImage.Format_RGBA8888
        )
        self.current_pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(self.current_pixmap)
        return True
