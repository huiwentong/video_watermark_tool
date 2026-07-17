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

        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.header_label = QLabel("No watermark selected")
        self.header_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; padding: 4px 0 6px 0; color: #8ab4d6;"
        )
        self.fav_btn = QPushButton("\u2606 Favorite")
        self.fav_btn.setFixedHeight(22)
        self.fav_btn.setStyleSheet(
            "QPushButton { background: #3a3a3a; border: 1px solid #5a5a5a; border-radius: 3px; "
            "padding: 2px 10px; color: #d4d4d4; font-size: 10px; font-weight: 500; }"
            "QPushButton:hover { background: #484848; border-color: #5dade2; }"
            "QPushButton:checked { background: #5a3c3c; border-color: #d98a3c; color: #f0c040; }"
        )
        self.fav_btn.setCheckable(True)
        self.fav_btn.setVisible(False)
        self.fav_btn.clicked.connect(self._on_fav_toggle)
        header_row.addWidget(self.header_label, 1)
        header_row.addWidget(self.fav_btn)
        layout.addLayout(header_row)

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

        self.opacity_slider = self._make_slider("Opacity", 0, 100, 100, "%", use_spinbox=True)
        layout.addWidget(self.opacity_slider)

        self.scale_slider = self._make_slider("Scale", 5, 500, 100, "%", use_spinbox=True)
        layout.addWidget(self.scale_slider)

        self.rotation_slider = self._make_slider("Rotation", -180, 180, 0, "°", use_spinbox=True)
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
        self.tile_spacing_spin = QSpinBox()
        self.tile_spacing_spin.setRange(0, 500)
        self.tile_spacing_spin.setValue(0)
        self.tile_spacing_spin.setSuffix(" px")
        self.tile_spacing_spin.setStyleSheet(
            "QSpinBox { color: #5dade2; font-weight: 500; min-width: 60px; "
            "font-size: 11px; background: #3c3c3c; border: 1px solid #4d4d4d; "
            "border-radius: 3px; padding: 2px 4px; }"
            "QSpinBox:focus { border-color: #5dade2; }"
        )
        self.tile_spacing_spin.valueChanged.connect(self._emit_changed)
        tile_layout.addRow("Spacing:", self.tile_spacing_spin)
        layout.addWidget(tile_group)

        layout.addStretch()

    def _update_fav_btn(self):
        if self._watermark is None:
            self.fav_btn.setVisible(False)
            return
        try:
            from app.redis_manager import is_favorited
            fav = is_favorited(self._watermark)
        except Exception:
            fav = False
        self.fav_btn.setVisible(True)
        self.fav_btn.blockSignals(True)
        if fav:
            self.fav_btn.setText("\u2605 Favorited")
            self.fav_btn.setChecked(True)
        else:
            self.fav_btn.setText("\u2606 Favorite")
            self.fav_btn.setChecked(False)
        self.fav_btn.blockSignals(False)

    def _on_fav_toggle(self, checked: bool):
        if self._watermark is None:
            return
        from app.redis_manager import save_favorite, remove_favorite
        if checked:
            save_favorite(self._watermark)
            self.fav_btn.setText("\u2605 Favorited")
        else:
            remove_favorite(self._watermark)
            self.fav_btn.setText("\u2606 Favorite")

    def onselectImage(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All files (*.*)"
        )
        if path:
            self.image_selector_text.setText(path)
            self._on_source_changed()

    def _make_slider(self, label: str, min_v: int, max_v: int,
                     default: int, suffix: str,
                     use_spinbox: bool = False) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(0, 1, 0, 1)
        wl.setSpacing(0)

        header = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; color: #b8b8b8; background: transparent;")

        if use_spinbox:
            from PySide6.QtWidgets import QSpinBox
            val = QSpinBox()
            val.setRange(min_v, max_v)
            val.setValue(default)
            val.setSuffix(suffix)
            val.setAlignment(Qt.AlignRight)
            val.setStyleSheet(
                "QSpinBox { color: #5dade2; font-weight: 500; min-width: 60px; "
                "font-size: 11px; background: #3c3c3c; border: 1px solid #4d4d4d; "
                "border-radius: 3px; padding: 2px 4px; }"
                "QSpinBox:focus { border-color: #5dade2; }"
                "QSpinBox::up-button, QSpinBox::down-button { border: none; "
                "background: #3a3a3a; width: 14px; }"
            )
        else:
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

        if use_spinbox:
            # Sync slider -> spinbox
            slider.valueChanged.connect(lambda v, sp=val: sp.setValue(v))
            # Sync spinbox -> slider
            val.valueChanged.connect(lambda v, sl=slider: sl.setValue(v))
            # Emit changed when either changes (spinbox covers both paths)
            val.valueChanged.connect(lambda: self._emit_changed())
            w._value_spin = val
        else:
            slider.valueChanged.connect(
                lambda v, vl=val, s=suffix: vl.setText(f"{v}{s}")
            )
            slider.valueChanged.connect(lambda: self._emit_changed())
            w._value_label = val

        wl.addWidget(slider)
        w._slider = slider
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
        self.opacity_slider._value_spin.setValue(wm.opacity)
        self.scale_slider._slider.setValue(wm.scale_percent)
        self.scale_slider._value_spin.setValue(wm.scale_percent)
        self.rotation_slider._slider.setValue(wm.rotation)
        self.rotation_slider._value_spin.setValue(wm.rotation)

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
        self.tile_spacing_spin.setValue(wm.tile_spacing)

        self._update_fav_btn()
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
        wm.tile_spacing = self.tile_spacing_spin.value()

        if(wm.wm_type == WatermarkType.IMAGE):
            wm.image_path = self.image_selector_text.text()
        else:
            wm.text_content = self.text_edit.text()
