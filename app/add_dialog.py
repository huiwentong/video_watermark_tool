from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QButtonGroup, QRadioButton
)
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt
from app.watermark import Watermark, WatermarkType


class AddWatermarkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Watermark")
        self.setMinimumWidth(460)
        self.result_watermark: Watermark = Watermark()
        self._selected_color = "#FFFFFF"
        self._setup_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #d4d4d4;
            }
            QLabel {
                color: #b8b8b8;
                font-size: 11px;
            }
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #4d4d4d;
                border-radius: 2px;
                padding: 5px 8px;
                color: #d4d4d4;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #5dade2;
            }
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4d4d4d;
                border-radius: 2px;
                padding: 5px 14px;
                color: #d4d4d4;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #484848;
                border-color: #5dade2;
            }
            QRadioButton {
                color: #d4d4d4;
                font-size: 12px;
                spacing: 6px;
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
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Add Watermark")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #8ab4d6; padding-bottom: 4px;")
        layout.addWidget(title)

        # type
        type_label = QLabel("Watermark Type:")
        type_label.setStyleSheet("font-weight: 500; color: #b8b8b8; padding-top: 4px;")
        layout.addWidget(type_label)

        type_row = QHBoxLayout()
        type_row.setSpacing(16)
        self.type_group = QButtonGroup(self)
        self.rb_image = QRadioButton("Image Watermark")
        self.rb_text = QRadioButton("Text Watermark")
        self.rb_image.setChecked(True)
        self.type_group.addButton(self.rb_image, 0)
        self.type_group.addButton(self.rb_text, 1)
        type_row.addWidget(self.rb_image)
        type_row.addWidget(self.rb_text)
        type_row.addStretch()
        layout.addLayout(type_row)

        # image path
        self.img_layout = QHBoxLayout()
        self.img_path_edit = QLineEdit()
        self.img_path_edit.setPlaceholderText("Select watermark image...")
        self.img_path_edit.setReadOnly(True)
        self.img_browse_btn = QPushButton("Browse\u2026")
        self.img_browse_btn.clicked.connect(self._browse_image)
        self.img_layout.addWidget(self.img_path_edit, 1)
        self.img_layout.addWidget(self.img_browse_btn)
        layout.addLayout(self.img_layout)

        # text content
        self.text_layout = QVBoxLayout()
        self.text_label = QLabel("Watermark Text:")
        self.text_edit = QLineEdit("watermark")
        self.text_edit.setPlaceholderText("Enter watermark text...")
        self.text_layout.addWidget(self.text_label)
        self.text_layout.addWidget(self.text_edit)
        for w in [self.text_label, self.text_edit]:
            w.setVisible(False)
        layout.addLayout(self.text_layout)

        # font color — color picker button
        self.color_layout = QHBoxLayout()
        self.color_label = QLabel("Font Color:")
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 28)
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self.color_btn.setToolTip("Click to pick a color")
        self._update_color_btn("#FFFFFF")
        self.color_btn.clicked.connect(self._pick_color)

        self.color_hex_label = QLabel("#FFFFFF")
        self.color_hex_label.setStyleSheet(
            "background: transparent; color: #b8b8b8; font-size: 11px; padding-left: 4px;"
        )

        self.color_layout.addWidget(self.color_label)
        self.color_layout.addWidget(self.color_btn)
        self.color_layout.addWidget(self.color_hex_label)
        self.color_layout.addStretch()
        for w in [self.color_label, self.color_btn, self.color_hex_label]:
            w.setVisible(False)
        layout.addLayout(self.color_layout)

        self.rb_image.toggled.connect(self._on_type_changed)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        ok_btn = QPushButton("Add")
        ok_btn.setStyleSheet(
            "QPushButton { background: #3d7eb7; color: white; font-weight: 600; "
            "border: none; border-radius: 2px; padding: 6px 20px; font-size: 12px; }"
            "QPushButton:hover { background: #4a8fc9; }"
        )
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self._accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _update_color_btn(self, hex_color: str):
        self.color_btn.setStyleSheet(
            f"QPushButton {{ background: {hex_color}; border: 1px solid #5a5a5a; "
            f"border-radius: 2px; }}"
            f"QPushButton:hover {{ border-color: #5dade2; }}"
        )

    def _pick_color(self):
        from PySide6.QtWidgets import QColorDialog
        initial = QColor(self._selected_color) if self._selected_color else QColor(255, 255, 255)
        color = QColorDialog.getColor(initial, self, "Select Font Color")
        if color.isValid():
            self._selected_color = color.name()
            self._update_color_btn(self._selected_color)
            self.color_hex_label.setText(self._selected_color)

    def _on_type_changed(self):
        is_img = self.rb_image.isChecked()
        for w in [self.img_path_edit, self.img_browse_btn]:
            w.setVisible(is_img)
        for w in [self.text_label, self.text_edit,
                  self.color_label, self.color_btn, self.color_hex_label]:
            w.setVisible(not is_img)

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All files (*.*)"
        )
        if path:
            self.img_path_edit.setText(path)

    def _accept(self):
        if self.rb_image.isChecked():
            path = self.img_path_edit.text().strip()
            if not path:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Notice", "Please select a watermark image")
                return
            self.result_watermark = Watermark(
                wm_type=WatermarkType.IMAGE, image_path=path
            )
        else:
            text = self.text_edit.text().strip()
            if not text:
                text = "watermark"
            self.result_watermark = Watermark(
                wm_type=WatermarkType.TEXT,
                text_content=text,
                font_color=self._selected_color,
            )
        self.accept()
