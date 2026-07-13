from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from app.watermark import Watermark, WatermarkType
from app.add_dialog import AddWatermarkDialog
from app.property_editor import WatermarkPropertyEditor


class WatermarkConsole(QWidget):
    watermarks_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.watermarks: list[Watermark] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid #3a3a3a;")
        tl = QHBoxLayout(title_bar)
        tl.setContentsMargins(8, 6, 8, 6)
        title = QLabel("Watermark Console")
        title.setStyleSheet("color: #8ab4d6; font-weight: 600; font-size: 12px; background: transparent;")
        tl.addWidget(title)
        tl.addStretch()
        layout.addWidget(title_bar)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)

        # list panel
        list_panel = QWidget()
        list_panel.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(6, 6, 6, 0)
        list_layout.setSpacing(6)

        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QListWidget.NoFrame)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #2e2e2e;
                border: 1px solid #3e3e3e;
                border-radius: 2px;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 7px 10px;
                border-bottom: 1px solid #353535;
                color: #c8c8c8;
            }
            QListWidget::item:hover {
                background: #363636;
            }
            QListWidget::item:selected {
                background: #3d7eb7;
                color: #ffffff;
            }
        """)
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.list_widget, 1)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.add_btn = QPushButton("+ Add Watermark")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #3c6e4a;
                color: #d4d4d4;
                font-weight: 500;
                padding: 6px 14px;
                border: none;
                border-radius: 2px;
                font-size: 11px;
            }
            QPushButton:hover { background: #4a8058; }
            QPushButton:pressed { background: #3c6e4a; }
        """)
        self.del_btn = QPushButton("\u2212 Delete")
        self.del_btn.setStyleSheet("""
            QPushButton {
                background: #5a3c3c;
                color: #d4d4d4;
                font-weight: 500;
                padding: 6px 14px;
                border: none;
                border-radius: 2px;
                font-size: 11px;
            }
            QPushButton:hover { background: #6e4a4a; }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.del_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._add_watermark)
        self.del_btn.clicked.connect(self._delete_watermark)

        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)

        splitter.addWidget(list_panel)

        self.property_editor = WatermarkPropertyEditor()
        self.property_editor.changed.connect(self._on_property_changed)
        splitter.addWidget(self.property_editor)

        splitter.setSizes([160, 320])
        layout.addWidget(splitter, 1)

    def _add_watermark(self):
        dlg = AddWatermarkDialog(self)
        if dlg.exec() == AddWatermarkDialog.Accepted:
            wm = dlg.result_watermark
            self.watermarks.append(wm)
            self._refresh_list()
            self.list_widget.setCurrentRow(len(self.watermarks) - 1)
            self.watermarks_changed.emit()

    def _delete_watermark(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.watermarks):
            return
        wm = self.watermarks[row]
        reply = QMessageBox.question(
            self, "Delete Watermark",
            f"Remove watermark \u00ab{self._item_label(wm)}\u00bb?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.watermarks.pop(row)
            self._refresh_list()
            self.watermarks_changed.emit()

    def _on_selection_changed(self, row: int):
        self.del_btn.setEnabled(0 <= row < len(self.watermarks))
        if 0 <= row < len(self.watermarks):
            self.property_editor.set_watermark(self.watermarks[row])
        else:
            self.property_editor.setEnabled(False)
            self.property_editor.header_label.setText("No watermark selected")

    def _on_property_changed(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.watermarks):
            self.property_editor.apply_to(self.watermarks[row])
            self._refresh_item(row)
            self.watermarks_changed.emit()

    def _refresh_list(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for wm in self.watermarks:
            item = QListWidgetItem(self._item_label(wm))
            item.setToolTip(self._item_tooltip(wm))
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        if self.list_widget.count() == 0:
            self.property_editor.setEnabled(False)
            self.property_editor.header_label.setText("No watermark selected")
            self.del_btn.setEnabled(False)

    def _refresh_item(self, row: int):
        if 0 <= row < len(self.watermarks):
            wm = self.watermarks[row]
            self.list_widget.item(row).setText(self._item_label(wm))
            self.list_widget.item(row).setToolTip(self._item_tooltip(wm))

    def _item_label(self, wm: Watermark) -> str:
        icon = "\U0001f5bc" if wm.wm_type == WatermarkType.IMAGE else "\U0001f524"
        name = wm.text_content if wm.wm_type == WatermarkType.TEXT else (
            wm.image_path.split("/")[-1].split("\\")[-1][:20])
        return f"{icon}  {name}"

    def _item_tooltip(self, wm: Watermark) -> str:
        t = "Image" if wm.wm_type == WatermarkType.IMAGE else "Text"
        return (f"Type: {t}\n"
                f"Opacity: {wm.opacity}%  |  Scale: {wm.scale_percent}%  |  Rotate: {wm.rotation}\u00b0\n"
                f"Position: {wm.position_preset.value}  |  Tiling: {wm.tiling_mode.value}")

    def get_watermarks(self) -> list[Watermark]:
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.watermarks):
            self.property_editor.apply_to(self.watermarks[row])
        return self.watermarks
