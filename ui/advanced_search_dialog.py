# ElektronKomponentlarUchoti/ui/advanced_search_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QLabel, QSpinBox,
                             QComboBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt


class AdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kengaytirilgan qidiruv")
        self.setMinimumWidth(450)
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.main_window_ref = parent

        self.name_search = QLineEdit()
        self.part_number_search = QLineEdit()
        self.manufacturer_search = QLineEdit() # Yangi qidiruv maydoni
        self.category_search_combo = QComboBox()
        self.project_search_combo = QComboBox()
        self.value_search = QLineEdit(); self.value_search.setPlaceholderText("Masalan: 10k, 100nF, LM358")

        qty_group = QGroupBox("Miqdori")
        qty_layout = QFormLayout(qty_group)
        self.quantity_min_spin = QSpinBox(); self.quantity_min_spin.setRange(-1, 999999); self.quantity_min_spin.setSpecialValueText("Min."); self.quantity_min_spin.setValue(-1)
        self.quantity_max_spin = QSpinBox(); self.quantity_max_spin.setRange(-1, 999999); self.quantity_max_spin.setSpecialValueText("Maks."); self.quantity_max_spin.setValue(-1)
        qty_layout.addRow(" Minimal:", self.quantity_min_spin)
        qty_layout.addRow(" Maksimal:", self.quantity_max_spin)

        self.low_stock_only_check = QCheckBox("Faqat kam qolganlar")
        if self.main_window_ref:
            self.low_stock_only_check.setChecked(self.main_window_ref.low_stock_checkbox.isChecked())

        self.form_layout.addRow("Nomi (o'z ichiga oladi):", self.name_search)
        self.form_layout.addRow("Qism raqami (o'z ichiga oladi):", self.part_number_search)
        self.form_layout.addRow("Ishlab chiqaruvchi (o'z ichiga oladi):", self.manufacturer_search) # Yangi qator
        self.form_layout.addRow("Kategoriya:", self.category_search_combo)
        self.form_layout.addRow("Loyiha:", self.project_search_combo)
        self.form_layout.addRow("Qiymati (o'z ichiga oladi):", self.value_search)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(qty_group)
        self.layout.addWidget(self.low_stock_only_check)

        self.button_box = QDialogButtonBox()
        self.ok_button = self.button_box.addButton("Qidirish", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton("Bekor qilish", QDialogButtonBox.RejectRole)
        self.reset_button = self.button_box.addButton("Tozalash", QDialogButtonBox.ResetRole)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.reset_button.clicked.connect(self.reset_filters)
        self.layout.addWidget(self.button_box)

        self._load_combobox_data()

    def _load_combobox_data(self):
        self.category_search_combo.addItem("Har qanday kategoriya", None)
        self.project_search_combo.addItem("Har qanday loyiha", None)
        self.project_search_combo.addItem("Loyihasiz", "")

        if self.main_window_ref:
            try:
                for i in range(self.main_window_ref.category_filter_combo.count()):
                    text = self.main_window_ref.category_filter_combo.itemText(i)
                    if text != "Barcha kategoriyalar":
                        self.category_search_combo.addItem(text, text)

                for i in range(self.main_window_ref.project_filter_combo.count()):
                    text = self.main_window_ref.project_filter_combo.itemText(i)
                    if text != "Barcha loyihalar":
                        if text.lower() != "loyihasiz":
                             self.project_search_combo.addItem(text, text)
            except Exception as e:
                print(f"Kengaytirilgan qidiruv uchun ro'yxatlarni yuklashda xatolik: {e}")

    def reset_filters(self):
        self.name_search.clear()
        self.part_number_search.clear()
        self.manufacturer_search.clear() # Yangi maydonni tozalash
        self.value_search.clear()
        self.category_search_combo.setCurrentIndex(0)
        self.project_search_combo.setCurrentIndex(0)
        self.quantity_min_spin.setValue(-1)
        self.quantity_max_spin.setValue(-1)
        if self.main_window_ref:
            self.low_stock_only_check.setChecked(self.main_window_ref.low_stock_checkbox.isChecked())
        else:
            self.low_stock_only_check.setChecked(False)

    def get_filters(self):
        filters = {}; has_active_filter = False

        if self.name_search.text().strip(): filters['adv_name'] = self.name_search.text().strip(); has_active_filter = True
        if self.part_number_search.text().strip(): filters['adv_part_number'] = self.part_number_search.text().strip(); has_active_filter = True
        if self.manufacturer_search.text().strip(): filters['adv_manufacturer'] = self.manufacturer_search.text().strip(); has_active_filter = True # Yangi filtr

        cat_data = self.category_search_combo.currentData()
        if cat_data is not None: filters['category_name'] = cat_data; has_active_filter = True

        proj_data = self.project_search_combo.currentData()
        if proj_data is not None: filters['project_name'] = proj_data; has_active_filter = True

        if self.value_search.text().strip(): filters['adv_value'] = self.value_search.text().strip(); has_active_filter = True
        if self.quantity_min_spin.value() != -1: filters['quantity_min'] = self.quantity_min_spin.value(); has_active_filter = True
        if self.quantity_max_spin.value() != -1: filters['quantity_max'] = self.quantity_max_spin.value(); has_active_filter = True

        main_low_stock_checked = self.main_window_ref.low_stock_checkbox.isChecked() if self.main_window_ref else False
        if self.low_stock_only_check.isChecked() != main_low_stock_checked:
            filters['low_stock_only'] = self.low_stock_only_check.isChecked()
            has_active_filter = True
        elif self.low_stock_only_check.isChecked():
            filters['low_stock_only'] = True
            has_active_filter = True

        return filters if has_active_filter else {}