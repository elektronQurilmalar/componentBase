# ElektronKomponentlarUchoti/ui/settings_dialog.py
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QFormLayout, QComboBox,
                             QCheckBox, QPushButton, QDialogButtonBox, QLabel,
                             QLineEdit, QHBoxLayout, QFileDialog, QMessageBox, QScrollArea,
                             QWidget, QListWidget, QListWidgetItem, QAbstractItemView,
                             QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
import os

try:
    from utils.config_manager import APP_SETTINGS, get_setting, set_setting, save_settings, load_settings
    from app_logic.db_manager import (_ensure_column_exists, get_db_connection, sanitize_column_name,
                                      get_all_possible_component_fields_info,
                                      drop_custom_column_from_components_table)  # drop_custom_column qo'shildi
except ImportError:
    print("XATOLIK: config_manager.py yoki db_manager.py topilmadi (settings_dialog.py).")
    APP_SETTINGS = {"theme": "Tizim (Yorqin)", "confirm_delete": True, "default_datasheet_dir": "",
                    "visible_columns": [], "column_headers_uz": {}, "custom_text_fields": []}
    _DEFAULT_LIGHT_THEME_NAME = "Tizim (Yorqin)";
    _DEFAULT_DARK_THEME_NAME = "Metall (Qorong'u)"


    def set_setting(key, value):
        print("Xatolik: Sozlama saqlanmadi."); return False


    def save_settings(s):
        print("Xatolik: Sozlamalar saqlanmadi."); return False


    def load_settings():
        return APP_SETTINGS


    def get_setting(key, default=None):
        return default


    def _ensure_column_exists(conn, table, col, type):
        pass


    def get_db_connection():
        return None


    def sanitize_column_name(name):
        return name.lower().replace(" ", "_")


    def get_all_possible_component_fields_info():
        return []


    def drop_custom_column_from_components_table(column_to_drop_db_key):
        print("MB XATOSI: Ustun o'chirilmadi"); return False


class SettingsDialog(QDialog):
    # (Bu klass o'zgarishsiz qoldi)
    def __init__(self, parent=None, available_themes=None):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        self.setMinimumWidth(550);
        self.setModal(True)
        self.main_window_ref = parent;
        self.ui_settings = load_settings().copy()
        self.main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self);
        scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget();
        self.form_layout = QFormLayout(self.scroll_widget)
        scroll_area.setWidget(self.scroll_widget);
        self.main_layout.addWidget(scroll_area)
        self.theme_combo = QComboBox()
        self.available_themes_list = available_themes
        if not self.available_themes_list:
            self.available_themes_list = [globals().get("_DEFAULT_LIGHT_THEME_NAME", "Tizim (Yorqin)"),
                                          globals().get("_DEFAULT_DARK_THEME_NAME", "Metall (Qorong'u)")]
        self.theme_combo.addItems(self.available_themes_list);
        self.form_layout.addRow(QLabel("Interfeys mavzusi:"), self.theme_combo)
        self.confirm_delete_checkbox = QCheckBox("Komponentni o'chirishdan oldin tasdiq so'ralsinmi?");
        self.form_layout.addRow(self.confirm_delete_checkbox)
        datasheet_dir_layout = QHBoxLayout();
        self.datasheet_dir_edit = QLineEdit();
        self.datasheet_dir_edit.setPlaceholderText("Papkani tanlang yoki yo'lni kiriting")
        datasheet_dir_button = QPushButton("...");
        datasheet_dir_button.setFixedWidth(30);
        datasheet_dir_button.clicked.connect(self.browse_datasheet_dir)
        datasheet_dir_layout.addWidget(self.datasheet_dir_edit);
        datasheet_dir_layout.addWidget(datasheet_dir_button)
        self.form_layout.addRow(QLabel("Standart Datasheet papkasi:"), datasheet_dir_layout)
        self.last_import_dir_label = QLabel(self.ui_settings.get("last_import_dir", "-"));
        self.form_layout.addRow(QLabel("Oxirgi import papkasi:"), self.last_import_dir_label)
        self.last_export_dir_label = QLabel(self.ui_settings.get("last_export_dir", "-"));
        self.form_layout.addRow(QLabel("Oxirgi eksport papkasi:"), self.last_export_dir_label)
        self.button_box = QDialogButtonBox();
        self.ok_button = self.button_box.addButton("OK (Saqlash)", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton("Bekor qilish", QDialogButtonBox.RejectRole);
        self.apply_button = self.button_box.addButton("Qo'llash", QDialogButtonBox.ApplyRole)
        self.button_box.accepted.connect(self.accept_settings);
        self.button_box.rejected.connect(self.reject);
        self.apply_button.clicked.connect(self.apply_settings_action)
        self.main_layout.addWidget(self.button_box);
        self.load_settings_to_ui()

    def load_settings_to_ui(self):
        default_theme_name = self.available_themes_list[0] if self.available_themes_list else "Tizim (Yorqin)"
        current_theme = self.ui_settings.get("theme", default_theme_name);
        idx = self.theme_combo.findText(current_theme)
        if idx != -1:
            self.theme_combo.setCurrentIndex(idx)
        else:
            if self.theme_combo.count() > 0: self.theme_combo.setCurrentIndex(0)
        self.confirm_delete_checkbox.setChecked(self.ui_settings.get("confirm_delete", True));
        self.datasheet_dir_edit.setText(self.ui_settings.get("default_datasheet_dir", ""))
        self.last_import_dir_label.setText(self.ui_settings.get("last_import_dir", "-"));
        self.last_export_dir_label.setText(self.ui_settings.get("last_export_dir", "-"))

    def browse_datasheet_dir(self):
        current_dir = self.datasheet_dir_edit.text()
        if not current_dir or not os.path.isdir(current_dir): current_dir = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "Standart Datasheet Papkasini Tanlang", current_dir)
        if directory: self.datasheet_dir_edit.setText(directory)

    def _apply_ui_to_settings_var(self):
        self.ui_settings["theme"] = self.theme_combo.currentText();
        self.ui_settings["confirm_delete"] = self.confirm_delete_checkbox.isChecked()
        self.ui_settings["default_datasheet_dir"] = self.datasheet_dir_edit.text().strip()

    def apply_settings_action(self):
        old_theme_from_app_settings = APP_SETTINGS.get("theme");
        self._apply_ui_to_settings_var();
        success = True
        for key, value in self.ui_settings.items():
            if key not in ["visible_columns", "column_headers_uz", "custom_text_fields"]:
                if not set_setting(key, value): success = False; break
        if success:
            print("Sozlamalar muvaffaqiyatli qo'llanildi.");
            new_theme_from_app_settings = APP_SETTINGS.get("theme")
            if old_theme_from_app_settings != new_theme_from_app_settings:
                QMessageBox.information(self, "Mavzu o'zgarishi",
                                        "Interfeys mavzusi o'zgarishi uchun dasturni qayta ishga tushiring.")
                if self.main_window_ref and hasattr(self.main_window_ref, 'apply_theme_from_main'):
                    self.main_window_ref.apply_theme_from_main(QApplication.instance(), new_theme_from_app_settings)
            return True
        else:
            QMessageBox.critical(self, "Xatolik", "Sozlamalarni saqlashda xatolik yuz berdi."); return False

    def accept_settings(self):
        if self.apply_settings_action(): super().accept()

    def reject(self):
        print("Sozlamalar oynasi bekor qilindi."); super().reject()


class ManageColumnsDialog(QDialog):
    # (Bu klass o'zgarishsiz qoldi)
    def __init__(self, parent, all_fields_info, current_visible_keys, current_headers_map_uz):
        super().__init__(parent);
        self.setWindowTitle("Jadval Ustunlarini Boshqarish");
        self.setMinimumWidth(400);
        self.setModal(True)
        self.all_fields_info = all_fields_info;
        self.current_visible_keys = list(current_visible_keys);
        self.current_headers_map_uz = dict(current_headers_map_uz)
        self.layout = QVBoxLayout(self);
        self.list_widget = QListWidget();
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.populate_list_widget();
        self.layout.addWidget(self.list_widget);
        self.button_box = QDialogButtonBox()
        self.ok_button = self.button_box.addButton("OK (Saqlash)", QDialogButtonBox.AcceptRole);
        self.cancel_button = self.button_box.addButton("Bekor qilish", QDialogButtonBox.RejectRole)
        self.button_box.accepted.connect(self.accept);
        self.button_box.rejected.connect(self.reject);
        self.layout.addWidget(self.button_box)

    def populate_list_widget(self):
        self.list_widget.clear()
        for db_key in self.current_visible_keys:  # Avval ko'rinadiganlar
            field_info = next((info for info in self.all_fields_info if info['db_key'] == db_key), None)
            if field_info:
                display_name = self.current_headers_map_uz.get(db_key, field_info['display_name_uz'])
                item = QListWidgetItem(f"{display_name} ({db_key})");
                item.setData(Qt.UserRole, db_key)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable);
                item.setCheckState(Qt.Checked);
                self.list_widget.addItem(item)
        for field_info in self.all_fields_info:  # Keyin yashirinlar
            if field_info['db_key'] not in self.current_visible_keys:
                display_name = self.current_headers_map_uz.get(field_info['db_key'], field_info['display_name_uz'])
                item = QListWidgetItem(f"{display_name} ({field_info['db_key']})");
                item.setData(Qt.UserRole, field_info['db_key'])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable);
                item.setCheckState(Qt.Unchecked);
                self.list_widget.addItem(item)

    def get_selected_columns_and_headers(self):
        new_visible_keys = [];
        new_headers_map_uz = {}
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                db_key = item.data(Qt.UserRole);
                new_visible_keys.append(db_key)
                full_text = item.text();
                display_name = full_text.split('(')[0].strip();
                new_headers_map_uz[db_key] = display_name
        if not new_visible_keys:
            id_field_info = next((info for info in self.all_fields_info if info['db_key'] == 'id'), None)
            if id_field_info:
                new_visible_keys.append('id');
                new_headers_map_uz['id'] = self.current_headers_map_uz.get('id', id_field_info['display_name_uz'])
                QMessageBox.warning(self, "Minimal Tanlov",
                                    "Hech qanday ustun tanlanmadi. Kamida 'ID' ustuni ko'rsatiladi.")
        return new_visible_keys, new_headers_map_uz


class ManageCustomFieldsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maxsus Matnli Maydonlarni Boshqarish")
        self.setMinimumWidth(500);
        self.setModal(True)
        self.main_window_ref = parent
        self.layout = QVBoxLayout(self)
        self.table_widget = QTableWidget();
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(
            ["Maydon Ko'rinadigan Nomi (O'zbekcha)", "Ma'lumotlar Bazasi Kaliti (Avto)"])
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table_widget)
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Yangi Maydon Qo'shish...");
        self.delete_button = QPushButton("Tanlangan Maydonni O'chirish")
        buttons_layout.addWidget(self.add_button);
        buttons_layout.addWidget(self.delete_button);
        buttons_layout.addStretch()
        self.layout.addLayout(buttons_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("OK (Yopish)");  # Saqlash har bir amalda bo'ladi
        self.button_box.button(QDialogButtonBox.Cancel).setText("Bekor qilish")
        self.layout.addWidget(self.button_box)
        self.add_button.clicked.connect(self.add_new_custom_field)
        self.delete_button.clicked.connect(self.delete_selected_custom_field)  # Endi ulanadi
        self.table_widget.itemSelectionChanged.connect(
            self.update_delete_button_state)  # O'chirish tugmasi holatini yangilash
        self.button_box.accepted.connect(self.accept);
        self.button_box.rejected.connect(self.reject)
        self._load_custom_fields_to_table();
        self.update_delete_button_state()  # Boshlang'ich holat

    def _load_custom_fields_to_table(self):
        self.table_widget.setRowCount(0)
        custom_fields = get_setting("custom_text_fields", [])
        for field_data in custom_fields:
            row_pos = self.table_widget.rowCount();
            self.table_widget.insertRow(row_pos)
            item_name = QTableWidgetItem(field_data['display_name_uz'])
            item_key = QTableWidgetItem(field_data['db_key'])
            item_key.setData(Qt.UserRole, field_data['db_key'])  # db_key ni UserRole da saqlash (o'chirish uchun)
            item_key.setFlags(item_key.flags() & ~Qt.ItemIsEditable)  # Kalitni tahrirlab bo'lmaydi
            self.table_widget.setItem(row_pos, 0, item_name)
            self.table_widget.setItem(row_pos, 1, item_key)
        self.update_delete_button_state()

    def update_delete_button_state(self):
        self.delete_button.setEnabled(bool(self.table_widget.selectedItems()))

    def add_new_custom_field(self):
        display_name, ok = QInputDialog.getText(self, "Yangi Maxsus Maydon",
                                                "Maydon uchun ko'rinadigan nom kiriting (masalan, Yetkazib Beruvchi):")
        if ok and display_name.strip():
            display_name = display_name.strip();
            db_key = sanitize_column_name(display_name)
            all_existing_db_keys = [f['db_key'] for f in get_all_possible_component_fields_info(
                include_fk_names=False)]  # Faqat haqiqiy MB ustunlari
            temp_key = db_key;
            counter = 1
            while temp_key in all_existing_db_keys:
                temp_key = f"{db_key}_{counter}";
                counter += 1
            db_key = temp_key
            current_custom_fields = get_setting("custom_text_fields", [])
            # Xuddi shunday display_name mavjudligini tekshirish (ixtiyoriy)
            if any(cf['display_name_uz'].lower() == display_name.lower() for cf in current_custom_fields):
                QMessageBox.warning(self, "Takrorlanuvchi Nom", f"'{display_name}' nomli maydon allaqachon mavjud.")
                return

            current_custom_fields.append({'db_key': db_key, 'display_name_uz': display_name})
            if set_setting("custom_text_fields", current_custom_fields):
                conn = get_db_connection()
                if conn: _ensure_column_exists(conn, 'components', db_key, 'TEXT'); conn.close()
                self._load_custom_fields_to_table()
                QMessageBox.information(self, "Muvaffaqiyatli",
                                        f"'{display_name}' nomli yangi maydon qo'shildi (Kalit: {db_key}).\nO'zgarishlar to'liq kuchga kirishi uchun dasturni qayta ishga tushirish tavsiya etiladi.")
                if self.main_window_ref: self.main_window_ref.refresh_all_data_and_filters()  # Asosiy oynani darhol yangilashga harakat
            else:
                QMessageBox.warning(self, "Xatolik", "Yangi maydonni sozlamalarga saqlashda xatolik.")
        elif ok and not display_name.strip():
            QMessageBox.warning(self, "Bo'sh Nom", "Maydon nomi bo'sh bo'lishi mumkin emas.")

    def delete_selected_custom_field(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Tanlanmagan", "O'chirish uchun maxsus maydonni tanlang.")
            return

        # Tanlangan qatorning db_key ni olish (ikkinchi ustundan)
        selected_row = self.table_widget.row(selected_items[0])
        db_key_item = self.table_widget.item(selected_row, 1)  # 1 - db_key ustuni
        display_name_item = self.table_widget.item(selected_row, 0)  # 0 - display_name ustuni

        if not db_key_item or not display_name_item:
            QMessageBox.critical(self, "Xatolik", "Tanlangan maydon ma'lumotlarini o'qib bo'lmadi.")
            return

        column_to_drop_db_key = db_key_item.text()
        column_to_drop_display_name = display_name_item.text()

        # Foydalanuvchidan tasdiq so'rash
        reply = QMessageBox.question(self, "O'chirishni Tasdiqlash",
                                     f"Haqiqatan ham '{column_to_drop_display_name}' ({column_to_drop_db_key}) maxsus maydonini o'chirmoqchimisiz?\n\n"
                                     f"DIQQAT: Bu amal ushbu maydondagi BARCHA ma'lumotlarni o'chirib yuboradi va bu jarayonni ORTQAGA QAYTARIB BO'LMAYDI!\n\n"
                                     f"Davom etasizmi?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 1. Sozlamalardan o'chirish
            current_custom_fields = get_setting("custom_text_fields", [])
            updated_custom_fields = [field for field in current_custom_fields if
                                     field['db_key'] != column_to_drop_db_key]

            if not set_setting("custom_text_fields", updated_custom_fields):
                QMessageBox.critical(self, "Xatolik", "Maxsus maydonni sozlamalardan o'chirishda xatolik yuz berdi.")
                return

            # 2. Ma'lumotlar bazasidan ustunni o'chirish
            if drop_custom_column_from_components_table(column_to_drop_db_key):
                QMessageBox.information(self, "Muvaffaqiyatli",
                                        f"'{column_to_drop_display_name}' maydoni va undagi ma'lumotlar muvaffaqiyatli o'chirildi.\nDasturni qayta ishga tushiring.")
                self._load_custom_fields_to_table()  # Jadvalni yangilash
                if self.main_window_ref: self.main_window_ref.refresh_all_data_and_filters()  # Asosiy oynani yangilash
            else:
                QMessageBox.critical(self, "MB Xatosi",
                                     f"'{column_to_drop_db_key}' ustunini ma'lumotlar bazasidan o'chirishda xatolik yuz berdi.\n"
                                     "Sozlamalar yangilandi, lekin MB o'zgarmadi. Muammolarni bartaraf etish uchun dasturchiga murojaat qiling yoki sozlamalar faylini qo'lda tahrirlang.")
                # Agar MB dan o'chirishda xato bo'lsa, sozlamalarni qaytarish yaxshiroq bo'lishi mumkin
                set_setting("custom_text_fields", current_custom_fields)  # Eski sozlamalarni qaytarish