import os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar,
    QApplication, QStatusBar
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

from app.preview_panel import PreviewPanel
from app.watermark_console import WatermarkConsole
from app.watermark_processor import WatermarkExporter


KATANA_STYLE = """
QMainWindow { background-color: #262626; }
QWidget {
    background-color: #262626;
    color: #d4d4d4;
    font-size: 12px;
}
QSplitter::handle {
    background: #3a3a3a;
    width: 3px;
}
QPushButton {
    background: #3a3a3a;
    border: 1px solid #4d4d4d;
    border-radius: 3px;
    padding: 5px 14px;
    color: #d4d4d4;
}
QPushButton:hover {
    background: #484848;
    border-color: #5dade2;
}
QPushButton:pressed {
    background: #3d7eb7;
}
QPushButton:disabled {
    background: #2e2e2e;
    color: #666;
    border-color: #3c3c3c;
}
QLineEdit {
    background: #3c3c3c;
    border: 1px solid #4d4d4d;
    border-radius: 3px;
    padding: 4px 6px;
    color: #d4d4d4;
    selection-background-color: #3d7eb7;
}
QLineEdit:focus {
    border-color: #5dade2;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #3a3a3a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #5dade2;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #7ebef2;
}
QSlider::sub-page:horizontal {
    background: #4a7fa0;
    border-radius: 2px;
}
QComboBox {
    background: #3c3c3c;
    border: 1px solid #4d4d4d;
    border-radius: 3px;
    padding: 4px 8px;
    color: #d4d4d4;
    min-height: 18px;
}
QComboBox:focus { border-color: #5dade2; }
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9a9a9a;
    margin-right: 4px;
}
QComboBox QAbstractItemView {
    background: #323232;
    border: 1px solid #4d4d4d;
    selection-background-color: #3d7eb7;
    selection-color: #ffffff;
    outline: none;
}
QGroupBox {
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    margin-top: 8px;
    padding: 12px 8px 8px 8px;
    font-weight: 500;
    color: #b8b8b8;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background: #262626;
    color: #8ab4d6;
}
QSpinBox {
    background: #3c3c3c;
    border: 1px solid #4d4d4d;
    border-radius: 3px;
    padding: 3px 6px;
    color: #d4d4d4;
    min-height: 18px;
}
QSpinBox:focus { border-color: #5dade2; }
QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: #3a3a3a;
    width: 16px;
}
QSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #9a9a9a;
    margin: 2px;
}
QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9a9a9a;
    margin: 2px;
}
QStatusBar {
    background: #1e1e1e;
    color: #9a9a9a;
    border-top: 1px solid #3a3a3a;
    font-size: 11px;
}
QScrollBar:vertical {
    background: #262626;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #4a4a4a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #5a5a5a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #262626;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #4a4a4a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #5a5a5a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QCheckBox {
    spacing: 6px;
    color: #d4d4d4;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #4d4d4d;
    border-radius: 2px;
    background: #3c3c3c;
}
QCheckBox::indicator:checked {
    background: #5dade2;
    border-color: #5dade2;
}
QRadioButton {
    spacing: 6px;
    color: #d4d4d4;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #4d4d4d;
    border-radius: 7px;
    background: #3c3c3c;
}
QRadioButton::indicator:checked {
    background: #5dade2;
    border-color: #5dade2;
}
QProgressBar {
    background: #3a3a3a;
    border: 1px solid #4d4d4d;
    border-radius: 3px;
    text-align: center;
    color: #d4d4d4;
    font-size: 11px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a7fa0, stop:1 #5dade2);
    border-radius: 2px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VibeWatermark - Video Watermark Tool")
        self.setMinimumSize(1100, 700)
        self.video_path: str = ""
        self._exporting = False

        font = QFont("Segoe UI", 9)
        QApplication.setFont(font)

        self._setup_ui()
        self.setStyleSheet(KATANA_STYLE)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)

        self.preview = PreviewPanel()
        self.preview.video_loaded.connect(self._on_video_loaded)
        splitter.addWidget(self.preview)

        self.console = WatermarkConsole()
        self.console.watermarks_changed.connect(self._refresh_preview)
        splitter.addWidget(self.console)

        splitter.setSizes([650, 360])
        main_layout.addWidget(splitter, 1)

        # bottom bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.export_btn = QPushButton("Export Video")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.setStyleSheet("""
            QPushButton#exportButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d98a3c, stop:1 #c97d30);
                color: #ffffff;
                font-weight: 600;
                padding: 7px 22px;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton#exportButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e89a4c, stop:1 #d98a3c);
            }
            QPushButton#exportButton:disabled {
                background: #3a3a3a;
                color: #666;
            }
        """)
        self.export_btn.clicked.connect(self._export_video)
        self.export_btn.setEnabled(False)

        self.export_img_btn = QPushButton("Export Image")
        self.export_img_btn.setObjectName("exportImageButton")
        self.export_img_btn.setStyleSheet("""
            QPushButton#exportImageButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a8a3c, stop:1 #4a7a30);
                color: #ffffff;
                font-weight: 600;
                padding: 7px 22px;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton#exportImageButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6a9a4c, stop:1 #5a8a3c);
            }
            QPushButton#exportImageButton:disabled {
                background: #3a3a3a;
                color: #666;
            }
        """)
        self.export_img_btn.clicked.connect(self._export_image)
        self.export_img_btn.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True)

        bottom_bar.addWidget(self.export_btn)
        bottom_bar.addWidget(self.export_img_btn)
        bottom_bar.addWidget(self.progress_bar, 1)

        main_layout.addLayout(bottom_bar)

        self.statusBar().showMessage("Ready \u2014 Load a video to begin")

    def _on_video_loaded(self, path: str):
        self.video_path = path
        ext = os.path.splitext(path)[1].lower()
        # print('video loaded!')
        img_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        is_img = ext in img_exts
        self.export_btn.setEnabled(not is_img)
        self.export_img_btn.setEnabled(True)
        self.statusBar().showMessage(f"Loaded: {Path(path).name}")
        self._refresh_preview()

    def _refresh_preview(self):
        if self.video_path:
            # print('refresh')
            watermarks = self.console.get_watermarks()
            print(watermarks)
            self.preview.update_preview(watermarks)
            count = len(watermarks)
            # for i in watermarks:
            #     print(i.to_dict())
            if count > 0:
                self.statusBar().showMessage(f"Video loaded  |  {count} watermark(s) active")

    def _export_video(self):
        if self._exporting or not self.video_path:
            return

        watermarks = self.console.get_watermarks()
        if not watermarks:
            QMessageBox.warning(self, "Notice", "Please add at least one watermark")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select output folder", os.path.dirname(self.video_path))
        if not output_dir:
            return

        input_name = Path(self.video_path).stem
        output_path = os.path.join(output_dir, f"{input_name}_watermarked.mp4")

        self._exporting = True
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Exporting video...")

        exporter = WatermarkExporter()

        class ExportWorker(QThread):
            progress = Signal(int)
            finished_signal = Signal(bool, str, str)

            def __init__(self, exporter, input_path, output_path, watermark, video_size):
                super().__init__()
                self.exporter: WatermarkExporter = exporter
                self.input_path = input_path
                self.output_path = output_path
                self.watermark = watermark
                self.video_size = video_size

            def run(self):
                success, err = self.exporter.export(
                    self.input_path, self.output_path,
                    self.watermark, self.video_size,
                    on_progress=self._on_progress
                )
                self.finished_signal.emit(success, self.output_path, err)

            def _on_progress(self, pct: int):
                self.progress.emit(pct)

        import cv2
        cap = cv2.VideoCapture(self.video_path)
        vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        self.worker = ExportWorker(
            exporter, self.video_path, output_path,
            self.preview.renderer.ori_wm_composite, (vw, vh, total_frames)
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self._on_export_finished)
        self.worker.start()

    def _on_export_finished(self, success: bool, output_path: str, err_msg: str):
        self._exporting = False
        self.export_btn.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.statusBar().showMessage(f"Export complete: {output_path}")
            QMessageBox.information(self, "Export successful",
                                    f"Video saved to:\n{output_path}")
        else:
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("Export failed")
            detail = f"ffmpeg command failed.\n\nError: {err_msg}"
            QMessageBox.critical(self, "Export Failed", detail)

        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))

    def _export_image(self):
        if self._exporting or not self.video_path:
            return

        watermarks = self.console.get_watermarks()
        if not watermarks:
            QMessageBox.warning(self, "Notice", "Please add at least one watermark")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select output folder", os.path.dirname(self.video_path))
        if not output_dir:
            return

        input_name = Path(self.video_path).stem
        output_path = os.path.join(output_dir, f"{input_name}_watermarked.png")

        self._exporting = True
        self.export_img_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Exporting image...")
        self.statusBar().showMessage("Exporting image...")

        QApplication.processEvents()

        success, err = self.preview.renderer.export_image(watermarks, output_path)

        self._exporting = False
        self.export_img_btn.setEnabled(True)
        ext = os.path.splitext(self.video_path)[1].lower()
        if ext not in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}:
            self.export_btn.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("100%")
            self.statusBar().showMessage(f"Image export complete: {output_path}")
            QMessageBox.information(self, "Export successful",
                                    f"Image saved to:\n{output_path}")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("")
            self.statusBar().showMessage("Image export failed")
            QMessageBox.critical(self, "Export Failed",
                                 f"Image export failed.\n\nError: {err}")

        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))

