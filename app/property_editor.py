from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QTextEdit, QFileDialog, QPushButton,QLineEdit,
    QComboBox, QSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt, Signal
from app.watermark import Watermark, PositionPreset, WatermarkType


class WatermarkPropertyEditor(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watermark: Watermark = None
        self._updating = False
        self.custom_x_spin = None
        self.custom_y_spin = None
        self._setup_ui()
        self.setEnabled(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(2)

        self.header_label = QLabel("No watermark selected")
        self.header_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; padding: 4px 0 6px 0; color: #8ab4d6;"
        )
        layout.addWidget(self.header_label)

        self.setStyleSheet("""
        QLabel {
            color: #dddddd;
            font-size: 13px;
        }

        QLineEdit {
            background-color: #2b2b2b;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px 8px;
            color: white;
            font-size: 13px;
        }

        QLineEdit:focus {
            border: 1px solid #4da3ff;
        }


        QPushButton {
            background-color: #3a7afe;
            color: white;
            border-radius: 5px;
            padding: 5px 15px;
            font-size: 13px;
        }

        QPushButton:hover {
            background-color: #5590ff;
        }

        QPushButton:pressed {
            background-color: #2865d9;
        }
        QPushButton:disabled {
            background-color: #444444;
            color: #888888;
            border: 1px solid #555555;
        }
        """)

        src_group = QGroupBox("source")
        src_layout = QVBoxLayout(src_group)
        src_layout.setSpacing(4)
        src_layout.setContentsMargins(4, 2, 4, 2)
        # Watermark Text
        self.text_edit_label = QLabel("WaterMark Text")
        self.text_edit = QLineEdit()
        self.text_edit.setFixedHeight(32)
        self.text_edit.setPlaceholderText("Enter watermark text...")
        self.text_edit.editingFinished.connect(self._on_source_changed)

        self.text_edit_label.setFixedWidth(120)


        self.text_edit_lay = QHBoxLayout()
        self.text_edit_lay.setSpacing(12)

        self.text_edit_lay.addWidget(self.text_edit_label)
        self.text_edit_lay.addWidget(self.text_edit)

        src_layout.addLayout(self.text_edit_lay)

        # Image Selector
        self.image_selector_button = QPushButton("Select Image")
        self.image_selector_button.setMinimumWidth(80)
        self.image_selector_button.setMaximumWidth(120)
        self.image_selector_button.setFixedHeight(32)
        self.image_selector_button.clicked.connect(self.onselectImage)

        self.image_selector_text = QLineEdit()
        self.image_selector_text.setFixedHeight(32)
        self.image_selector_text.editingFinished.connect(self._on_source_changed)
        self.image_selector_text.setPlaceholderText("choose image path...")

        self.image_selector_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        self.image_selector_text.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.image_selector_lay = QHBoxLayout()
        self.image_selector_lay.setSpacing(12)

        self.image_selector_lay.addWidget(self.image_selector_button)
        self.image_selector_lay.addWidget(self.image_selector_text)

        src_layout.addLayout(self.image_selector_lay)
        layout.addWidget(src_group)

        self.opacity_slider = self._make_slider("Opacity", 0, 100, 100, "%")
        layout.addWidget(self.opacity_slider)

        self.scale_slider = self._make_slider("Scale", 5, 500, 100, "%")
        layout.addWidget(self.scale_slider)

        self.rotation_slider = self._make_slider("Rotation", -180, 180, 0, "\u00b0")
        layout.addWidget(self.rotation_slider)


        # position
        pos_group = QGroupBox("Position")
        pos_group.setStyleSheet(
            "QGroupBox { border: 1px solid #4a4a4a; border-radius: 2px; "
            "margin-top: 6px; padding: 12px 6px 4px 6px; font-size: 11px; color: #b8b8b8; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
            "left: 8px; padding: 0 4px; background: #262626; color: #8ab4d6; }"
        )
        pos_layout = QFormLayout(pos_group)
        pos_layout.setSpacing(4)
        pos_layout.setContentsMargins(4, 2, 4, 2)
        self.pos_combo = QComboBox()
        label_map = {
            PositionPreset.TOP_LEFT: "Top Left",
            PositionPreset.TOP_CENTER: "Top Center",
            PositionPreset.TOP_RIGHT: "Top Right",
            PositionPreset.CENTER_LEFT: "Center Left",
            PositionPreset.CENTER: "Center",
            PositionPreset.CENTER_RIGHT: "Center Right",
            PositionPreset.BOTTOM_LEFT: "Bottom Left",
            PositionPreset.BOTTOM_CENTER: "Bottom Center",
            PositionPreset.BOTTOM_RIGHT: "Bottom Right",
            PositionPreset.CUSTOM: "Custom",
        }
        for p in PositionPreset:
            self.pos_combo.addItem(label_map.get(p, p.value), p.value)
        self.pos_combo.currentIndexChanged.connect(self._on_pos_changed)
        pos_layout.addRow("Preset:", self.pos_combo)

        self.custom_x_spin = QSpinBox()
        self.custom_x_spin.setRange(0, 99999)
        self.custom_y_spin = QSpinBox()
        self.custom_y_spin.setRange(0, 99999)
        self.custom_x_spin.valueChanged.connect(self._emit_changed)
        self.custom_y_spin.valueChanged.connect(self._emit_changed)
        pos_layout.addRow("X:", self.custom_x_spin)
        pos_layout.addRow("Y:", self.custom_y_spin)
        self._set_custom_visible(False)
        layout.addWidget(pos_group)

        # tiling
        tile_group = QGroupBox("Tiling")
        tile_group.setStyleSheet(
            "QGroupBox { border: 1px solid #4a4a4a; border-radius: 2px; "
            "margin-top: 6px; padding: 12px 6px 4px 6px; font-size: 11px; color: #b8b8b8; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
            "left: 8px; padding: 0 4px; background: #262626; color: #8ab4d6; }"
        )
        tile_layout = QFormLayout(tile_group)
        tile_layout.setSpacing(4)
        tile_layout.setContentsMargins(4, 2, 4, 2)
        self.tile_combo = QComboBox()
        from app.watermark import TilingMode
        self.tile_combo.addItem("None", TilingMode.NONE.value)
        self.tile_combo.addItem("Tile", TilingMode.TILE.value)
        self.tile_combo.addItem("Fill Frame", TilingMode.FILL.value)
        self.tile_combo.currentIndexChanged.connect(self._emit_changed)
        tile_layout.addRow("Mode:", self.tile_combo)
        layout.addWidget(tile_group)

        layout.addStretch()

    def onselectImage(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All files (*.*)"
        )
        if path:
            self.image_selector_text.setText(path)
            self._on_source_changed()

    def _make_slider(self, label: str, min_v: int, max_v: int,
                     default: int, suffix: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(0, 1, 0, 1)
        wl.setSpacing(0)

        header = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; color: #b8b8b8; background: transparent;")
        val = QLabel(f"{default}{suffix}")
        val.setAlignment(Qt.AlignRight)
        val.setStyleSheet(
            "color: #5dade2; font-weight: 500; min-width: 36px; "
            "font-size: 11px; background: transparent;"
        )
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(val)
        wl.addLayout(header)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(default)
        slider.valueChanged.connect(
            lambda v, vl=val, s=suffix: vl.setText(f"{v}{s}")
        )
        slider.valueChanged.connect(lambda: self._emit_changed())
        wl.addWidget(slider)
        w._slider = slider
        w._value_label = val
        return w

    def _on_pos_changed(self):
        is_custom = self.pos_combo.currentData() == PositionPreset.CUSTOM.value
        self._set_custom_visible(is_custom)
        self._emit_changed()


    def _on_source_changed(self):
        self._emit_changed()

    def _set_custom_visible(self, visible: bool):
        if self.custom_x_spin:
            self.custom_x_spin.setVisible(visible)
        if self.custom_y_spin:
            self.custom_y_spin.setVisible(visible)

    def _emit_changed(self):
        if not self._updating:
            self.changed.emit()

    def set_watermark(self, wm: Watermark):
        self._watermark = wm
        self._updating = True
        self.setEnabled(True)

        type_str = "Image" if wm.wm_type.name == "IMAGE" else "Text"
        self.header_label.setText(f"{type_str} Watermark  \u2014  {wm.id}")

        self.opacity_slider._slider.setValue(wm.opacity)
        self.opacity_slider._value_label.setText(f"{wm.opacity}%")
        self.scale_slider._slider.setValue(wm.scale_percent)
        self.scale_slider._value_label.setText(f"{wm.scale_percent}%")
        self.rotation_slider._slider.setValue(wm.rotation)
        self.rotation_slider._value_label.setText(f"{wm.rotation}{chr(176)}")

        if(wm.wm_type == WatermarkType.IMAGE):
            self.image_selector_button.setEnabled(True)
            self.image_selector_text.setEnabled(True)
            self.text_edit.setEnabled(False)
            self.image_selector_text.setText(wm.image_path)
            self.text_edit.setText('')
        else:
            self.image_selector_text.setText("")
            self.text_edit.setText(wm.text_content)
            self.text_edit.setEnabled(True)
            self.image_selector_button.setEnabled(False)
            self.image_selector_text.setEnabled(False)

        idx = self.pos_combo.findData(wm.position_preset.value)
        if idx >= 0:
            self.pos_combo.setCurrentIndex(idx)
        self.custom_x_spin.setValue(wm.custom_x)
        self.custom_y_spin.setValue(wm.custom_y)

        from app.watermark import TilingMode
        idx = self.tile_combo.findData(wm.tiling_mode.value)
        if idx >= 0:
            self.tile_combo.setCurrentIndex(idx)

        self._updating = False

    def apply_to(self, wm: Watermark):
        if self._watermark is None:
            return
        wm.opacity = self.opacity_slider._slider.value()
        wm.scale_percent = self.scale_slider._slider.value()
        wm.rotation = self.rotation_slider._slider.value()
        pos_val = self.pos_combo.currentData()
        wm.position_preset = PositionPreset(pos_val)
        wm.custom_x = self.custom_x_spin.value()
        wm.custom_y = self.custom_y_spin.value()
        from app.watermark import TilingMode
        tile_val = self.tile_combo.currentData()
        wm.tiling_mode = TilingMode(tile_val)

        if(wm.wm_type == WatermarkType.IMAGE):
            wm.image_path = self.image_selector_text.text()
        else:
            wm.text_content = self.text_edit.text()
