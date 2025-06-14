# ElektronKomponentlarUchoti/ui/add_component_dialog.py
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QTextEdit, QSpinBox, QLabel,
                             QComboBox, QHBoxLayout, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy,
                             QDateEdit)
from PyQt5.QtCore import Qt, QStandardPaths, QDate, QTimer

try:
    from app_logic.db_manager import (get_all_categories_names, get_all_package_types_names,
                                      get_all_storage_locations_names, get_component_by_id,
                                      get_all_possible_component_fields_info)
    from utils.config_manager import get_setting
except ImportError:
    print("XATOLIK: db_manager.py yoki config_manager.py import qilinmadi (add_component_dialog.py).")


    def get_all_categories_names():
        return ["MB Xato: Kat."]


    def get_all_package_types_names():
        return ["MB Xato: Pkg."]


    def get_all_storage_locations_names():
        return ["MB Xato: Joy."]


    def get_component_by_id(id):
        return None


    def get_all_possible_component_fields_info():
        return []


    def get_setting(key, default=None):
        return default

try:
    from utils.component_packages import get_packages_for_type
except ImportError:
    print("OGOHLANTIRISH: utils/component_packages.py topilmadi.")
    get_packages_for_type = lambda cat: get_all_package_types_names()


class AddComponentDialog(QDialog):
    def __init__(self, parent=None, component_id_to_edit=None):
        super().__init__(parent)

        self.component_id_to_edit = component_id_to_edit
        self.existing_data = None
        self.close_on_error = False
        self.main_window_ref = parent

        self.visible_db_keys = get_setting("visible_columns", [])
        if not self.visible_db_keys:
            all_fields = get_all_possible_component_fields_info()
            self.visible_db_keys = [field['db_key'] for field in all_fields if field.get('default_visible', True)]

        self.all_fields_info = {field['db_key']: field for field in get_all_possible_component_fields_info()}
        self.field_widgets = {}

        if self.component_id_to_edit:
            self.setWindowTitle("Komponentni Tahrirlash")
            try:
                self.existing_data = get_component_by_id(self.component_id_to_edit)
                if not self.existing_data:
                    QMessageBox.critical(self, "Xatolik", f"ID={self.component_id_to_edit} bilan komponent topilmadi.")
                    self.close_on_error = True
                    return
            except Exception as e:
                print(f"Komponentni olishda xatolik: {e}")
                QMessageBox.critical(self, "Xatolik", f"Komponent ma'lumotlarini yuklashda xatolik: {e}")
                self.close_on_error = True
                return
        else:
            self.setWindowTitle("Yangi Komponent Qo'shish")

        self.setMinimumWidth(500)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Dinamik ravishda maydonlarni yaratish
        self._create_dynamic_fields()

        self.layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton("Saqlash", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton("Bekor qilish", QDialogButtonBox.RejectRole)
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        if 'name' in self.field_widgets and isinstance(self.field_widgets['name'], QLineEdit):
            self.field_widgets['name'].textChanged.connect(self.toggle_save_button_state)

        self._load_combobox_data_for_visible_fields()

        if self.existing_data:
            self.load_data_into_fields(self.existing_data)
        else:
            if 'category_name' in self.field_widgets and isinstance(self.field_widgets['category_name'], QComboBox):
                self.field_widgets['category_name'].setCurrentIndex(-1)
                self._update_package_combo_based_on_category(None)
            if 'reminder_date' in self.field_widgets and isinstance(self.field_widgets['reminder_date'], QDateEdit):
                self.field_widgets['reminder_date'].setDate(QDate())

        if 'category_name' in self.field_widgets and isinstance(self.field_widgets['category_name'], QComboBox):
            self.field_widgets['category_name'].currentTextChanged.connect(self._update_package_combo_based_on_category)

        self.toggle_save_button_state()

    def _create_dynamic_fields(self):
        # --- YANNGI O'ZGARTIRISH: Kategoriya va Korpus maydonlarini majburiy qo'shish ---
        # Bu maydonlar endi sozlamalardan qat'i nazar har doim ko'rsatiladi.
        essential_field_keys = ['category_name', 'package_type_name']

        # 1. Avval majburiy maydonlarni yaratamiz
        for db_key in essential_field_keys:
            # Haqiqiy db_key ni topish (masalan, category_name uchun category_id)
            field_info = next(
                (info for info in self.all_fields_info.values() if info.get('related_name_key') == db_key), None)
            if not field_info:
                # Agar topilmasa, to'g'ridan-to'g'ri db_key bo'yicha qidirish
                field_info = self.all_fields_info.get(db_key)

            if not field_info:
                print(f"OGOHLANTIRISH: Majburiy maydon '{db_key}' uchun ma'lumot topilmadi.")
                continue

            label_text = field_info['display_name_uz']
            if field_info.get('required', False): label_text += "*"
            label = QLabel(label_text + ":")

            # Bu maydonlar har doim ComboBox bo'lishi kerak
            widget = QComboBox()
            widget.setEditable(True)
            widget.setInsertPolicy(QComboBox.NoInsert)

            self.field_widgets[db_key] = widget
            self.form_layout.addRow(label, widget)

        # 2. Keyin sozlamalardagi qolgan maydonlarni yaratamiz
        for db_key in self.visible_db_keys:
            # Agar maydon allaqachon majburiy sifatida yaratilgan bo'lsa, o'tkazib yuborish
            if db_key in essential_field_keys or db_key in ['category_id', 'package_type_id']:
                continue

            field_info = self.all_fields_info.get(db_key)
            if not field_info:
                print(f"OGOHLANTIRISH: '{db_key}' uchun maydon ma'lumoti topilmadi. O'tkazib yuborildi.")
                continue

            label_text = field_info['display_name_uz']
            if field_info.get('required', False): label_text += "*"
            label = QLabel(label_text + ":")
            widget = None
            field_type = field_info['type']

            if field_type == 'text':
                widget = QLineEdit()
                if db_key == 'datasheet_path':
                    widget.setPlaceholderText("Fayl yo'li yoki URL (bir nechta ';')")
                elif db_key == 'reminder_text':
                    widget.setPlaceholderText("Nima haqida eslatma?")
            elif field_type == 'text_area':
                widget = QTextEdit();
                widget.setFixedHeight(60)
            elif field_type == 'integer':
                widget = QSpinBox();
                widget.setRange(0, 999999 if db_key == 'quantity' else 99999);
                widget.setMinimumWidth(100)
            elif field_type == 'date':
                widget = QDateEdit(calendarPopup=True);
                widget.setSpecialValueText(" ");
                widget.setDate(QDate());
                widget.setMinimumDate(QDate(1900, 1, 1));
                widget.setMinimumWidth(120)
            elif field_type == 'fk_location':
                widget = QComboBox();
                widget.setEditable(True);
                widget.setInsertPolicy(QComboBox.NoInsert)
            elif field_type == 'file_path':
                datasheet_input = QLineEdit();
                datasheet_input.setPlaceholderText("Fayl yo'li yoki URL (bir nechta ';')")
                browse_button = QPushButton("Fayl tanlash...");
                browse_button.clicked.connect(self._browse_datasheet_file_action)
                h_layout = QHBoxLayout();
                h_layout.addWidget(datasheet_input);
                h_layout.addWidget(browse_button)
                self.form_layout.addRow(label, h_layout);
                self.field_widgets[db_key] = datasheet_input;
                continue
            elif field_type in ['timestamp', 'integer_pk', 'fk_category', 'fk_package']:
                continue
            else:
                widget = QLineEdit()

            if widget:
                self.field_widgets[db_key] = widget
                if db_key == 'quantity' and 'min_quantity' in self.visible_db_keys:
                    min_qty_field_info = self.all_fields_info.get('min_quantity');
                    min_qty_label_text = min_qty_field_info['display_name_uz']
                    if min_qty_field_info.get('required', False): min_qty_label_text += "*"
                    min_qty_widget = QSpinBox();
                    min_qty_widget.setRange(0, 99999);
                    min_qty_widget.setMinimumWidth(100)
                    self.field_widgets['min_quantity'] = min_qty_widget
                    h_layout = QHBoxLayout();
                    h_layout.addWidget(label);
                    h_layout.addWidget(widget)
                    h_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
                    h_layout.addWidget(QLabel(min_qty_label_text + ":"));
                    h_layout.addWidget(min_qty_widget)
                    self.form_layout.addRow(h_layout)
                elif db_key == 'min_quantity' and 'quantity' in self.field_widgets:
                    pass
                elif db_key == 'reminder_date' and 'reminder_text' in self.visible_db_keys:
                    reminder_text_field_info = self.all_fields_info.get('reminder_text');
                    reminder_text_label_text = reminder_text_field_info['display_name_uz']
                    if reminder_text_field_info.get('required', False): reminder_text_label_text += "*"
                    reminder_text_widget = QLineEdit();
                    reminder_text_widget.setPlaceholderText("Nima haqida eslatma?")
                    self.field_widgets['reminder_text'] = reminder_text_widget
                    h_layout = QHBoxLayout();
                    h_layout.addWidget(label);
                    h_layout.addWidget(widget)
                    h_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
                    h_layout.addWidget(QLabel(reminder_text_label_text + ":"));
                    h_layout.addWidget(reminder_text_widget, 1)
                    self.form_layout.addRow(h_layout)
                elif db_key == 'reminder_text' and 'reminder_date' in self.field_widgets:
                    pass
                else:
                    self.form_layout.addRow(label, widget)
        # --- O'ZGARTIRISH TUGADI ---

    def _load_combobox_data_for_visible_fields(self):
        if 'category_name' in self.field_widgets and isinstance(self.field_widgets['category_name'], QComboBox):
            combo = self.field_widgets['category_name']
            combo.blockSignals(True)
            combo.clear();
            combo.addItems(get_all_categories_names());
            combo.setCurrentIndex(-1)
            combo.blockSignals(False)

        if 'package_type_name' in self.field_widgets:
            self._update_package_combo_based_on_category(None)

        if 'location_name' in self.field_widgets and isinstance(self.field_widgets['location_name'], QComboBox):
            combo = self.field_widgets['location_name']
            combo.blockSignals(True)
            combo.clear();
            combo.addItems(get_all_storage_locations_names());
            combo.setCurrentIndex(-1)
            combo.blockSignals(False)

    def _update_package_combo_based_on_category(self, category_name_str):
        if 'package_type_name' not in self.field_widgets or \
                not isinstance(self.field_widgets['package_type_name'], QComboBox) or \
                'category_name' not in self.field_widgets or \
                not isinstance(self.field_widgets['category_name'], QComboBox):
            return

        package_combo = self.field_widgets['package_type_name']
        package_combo.blockSignals(True)
        current_package_text = package_combo.currentText()
        package_combo.clear()

        packages_to_load = []
        if category_name_str and category_name_str.strip():
            packages_to_load = get_packages_for_type(category_name_str)
        else:
            packages_to_load = get_all_package_types_names()

        if not packages_to_load: packages_to_load = ["Boshqa"]
        package_combo.addItems(packages_to_load)

        idx = package_combo.findText(current_package_text, Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if idx != -1:
            package_combo.setCurrentIndex(idx)
        else:
            package_combo.setCurrentIndex(-1)
        package_combo.blockSignals(False)

    def toggle_save_button_state(self):
        if hasattr(self, 'save_button') and self.save_button:
            if 'name' in self.field_widgets and isinstance(self.field_widgets['name'], QLineEdit):
                self.save_button.setEnabled(bool(self.field_widgets['name'].text().strip()))
            else:
                self.save_button.setEnabled(True)

    def _browse_datasheet_file_action(self):
        if 'datasheet_path' not in self.field_widgets or \
                not isinstance(self.field_widgets['datasheet_path'], QLineEdit):
            return

        datasheet_input_widget = self.field_widgets['datasheet_path']
        default_dir_setting = get_setting("default_datasheet_dir", "")
        start_dir = default_dir_setting if default_dir_setting and os.path.isdir(default_dir_setting) \
            else QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        current_paths_str = datasheet_input_widget.text().strip()
        file_path, _ = QFileDialog.getOpenFileName(self, "Datasheet faylini tanlang", start_dir,
                                                   "PDF fayllari (*.pdf);;Barcha fayllar (*)")
        if file_path:
            if current_paths_str:
                datasheet_input_widget.setText(current_paths_str + ";" + file_path)
            else:
                datasheet_input_widget.setText(file_path)

    def _set_combobox_text_carefully(self, combobox_widget, text_value):
        if not isinstance(combobox_widget, QComboBox): return

        combobox_widget.blockSignals(True)
        if text_value is None: text_value = ""
        idx = combobox_widget.findText(text_value, Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if idx != -1:
            combobox_widget.setCurrentIndex(idx)
        elif combobox_widget.isEditable():
            combobox_widget.setCurrentText(text_value)
        elif combobox_widget.count() > 0:
            combobox_widget.setCurrentIndex(-1)
        else:
            combobox_widget.setCurrentText("")
        combobox_widget.blockSignals(False)

    def load_data_into_fields(self, data_dict):
        try:
            # Kategoriya o'rnatilgandan so'ng paketlar ro'yxatini yangilash
            if 'category_name' in self.field_widgets and self.existing_data.get('category_name'):
                self._update_package_combo_based_on_category(self.existing_data['category_name'])

            for db_key, widget in self.field_widgets.items():
                value_to_set = data_dict.get(db_key)

                if db_key == 'category_name':
                    value_to_set = data_dict.get('category_name')
                elif db_key == 'package_type_name':
                    value_to_set = data_dict.get('package_type_name')
                elif db_key == 'location_name':
                    value_to_set = data_dict.get('location_name')

                if isinstance(widget, QLineEdit):
                    widget.setText(str(value_to_set) if value_to_set is not None else '')
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(str(value_to_set) if value_to_set is not None else '')
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value_to_set or 0))
                elif isinstance(widget, QDateEdit):
                    if value_to_set:
                        q_date = QDate.fromString(str(value_to_set), "yyyy-MM-dd")
                        widget.setDate(q_date if q_date.isValid() else QDate())
                    else:
                        widget.setDate(QDate())
                elif isinstance(widget, QComboBox):
                    if db_key == 'package_type_name':
                        QTimer.singleShot(10, lambda w=widget, v=value_to_set: self._set_combobox_text_carefully(w, v))
                    else:
                        self._set_combobox_text_carefully(widget, str(value_to_set) if value_to_set is not None else '')
        except Exception as e:
            print(f"Maydonlarga ma'lumotlarni yuklashda xato: {e}")
            QMessageBox.critical(self, "Xatolik", f"Dialog maydonlariga ma'lumotlarni yuklashda xatolik:\n{e}")
            self.close_on_error = True

    def get_data_from_fields(self):
        data = {}
        for db_key, widget in self.field_widgets.items():
            value = None
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText().strip()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QDateEdit):
                q_date = widget.date()
                if q_date.isValid() and not widget.text().strip() == "":
                    value = q_date.toString("yyyy-MM-dd")
                else:
                    value = None
            elif isinstance(widget, QComboBox):
                value = widget.currentText().strip()

            if db_key == 'category_name':
                data['category'] = value
            elif db_key == 'package_type_name':
                data['package_type'] = value
            elif db_key == 'location_name':
                data['location'] = value
            else:
                data[db_key] = value

        if 'min_quantity' not in self.field_widgets and 'min_quantity' not in data: data['min_quantity'] = 0
        if 'quantity' not in self.field_widgets and 'quantity' not in data: data['quantity'] = 0
        return data

    def validate_and_accept(self):
        component_data = self.get_data_from_fields()

        if 'name' in self.field_widgets and not component_data.get('name'):
            QMessageBox.warning(self, "Xatolik", "Komponent nomi kiritilishi shart!")
            self.field_widgets['name'].setFocus();
            return

        for db_key, field_info in self.all_fields_info.items():
            # Endi tekshiruvda `self.field_widgets` ni ishlatamiz, chunki maydonlar endi aralash tartibda bo'lishi mumkin
            if db_key in self.field_widgets and field_info.get('required', False):
                widget = self.field_widgets.get(db_key)
                if isinstance(widget, QComboBox):
                    if widget.currentIndex() == -1 and not widget.currentText().strip():
                        QMessageBox.warning(self, "Xatolik",
                                            f"'{field_info['display_name_uz']}' tanlanishi yoki kiritilishi shart!")
                        widget.setFocus();
                        return
                elif not component_data.get(db_key):
                    QMessageBox.warning(self, "Xatolik",
                                        f"'{field_info['display_name_uz']}' maydoni to'ldirilishi shart!")
                    widget.setFocus();
                    return
        super().accept()

    def check_initialization_error(self):
        return self.close_on_error