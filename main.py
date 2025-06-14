# ElektronKomponentlarUchoti/main.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLineEdit, QHeaderView, QAbstractItemView, QLabel, QSpacerItem,
                             QSizePolicy, QGroupBox, QAction, QStatusBar, QMessageBox, QDialog,
                             QComboBox, QFileDialog, QMenu, QCheckBox, QDialogButtonBox, QListWidget,
                             QStyleFactory)
from PyQt5.QtCore import Qt, QUrl, QDate
from PyQt5.QtGui import QIcon, QDesktopServices, QColor, QPalette, QLinearGradient, QBrush

# config_manager ni birinchi import qilish muhim
from utils.config_manager import load_settings, save_settings, get_setting, set_setting, DEFAULT_SETTINGS


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    path_to_resource = os.path.join(base_path, relative_path)
    return path_to_resource


from ui.add_component_dialog import AddComponentDialog
from ui.manage_locations_dialog import ManageLocationsDialog
from ui_logic.table_manager import TableManager
from ui.settings_dialog import SettingsDialog, ManageColumnsDialog, ManageCustomFieldsDialog

try:
    from app_logic.db_manager import (create_tables, get_all_components, delete_component,
                                      get_all_categories_names, add_component, update_component,
                                      get_distinct_project_names, get_all_possible_component_fields_info,
                                      _ensure_column_exists, sanitize_column_name)
    from app_logic.actions import (delete_selected_components, search_selected_component_online,
                                   export_data_dialog, generate_label_for_selected,
                                   generate_order_list_action, perform_project_revision_action)
    # config_manager allaqachon yuqorida import qilingan
except ImportError as e:
    print(f"XATOLIK: Kerakli modullarni import qilishda muammo: {e}")
    # QApplication yaratilmasdan oldin QMessageBox ni ishlatib bo'lmaydi,
    # shuning uchun bu yerda print bilan cheklanamiz yoki sys.exit(1) qilamiz.
    # Agar GUI ishga tushmasidan oldin xatolik bo'lsa, uni konsolda ko'rsatish yaxshiroq.
    # QMessageBox.critical(None, "Kritik Xatolik", f"Dastur modullarini yuklashda xatolik:\n{e}\n\nDastur yopiladi.")
    sys.exit(f"KRITIK XATOLIK: Dastur modullarini yuklashda muammo: {e}. Dastur to'xtatildi.")

YORQIN_MAVZU_NOMI = "Tizim (Yorqin)"
QORONGU_MAVZU_NOMI = "Metall (Qorong'u)"  # Qorong'u mavzu uchun stilni bu yerga qo'shing

DARK_STYLE_SHEET = """
QWidget {
    background-color: #4a4a4a; color: #e0e0e0; border-color: #606060;
    font-family: "Segoe UI", Arial, sans-serif;
}
QMainWindow { background-color: #404040; }
QMenuBar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #555555, stop:1 #484848);
    color: #e0e0e0; border-bottom: 1px solid #303030;
}
QMenuBar::item { background-color: transparent; padding: 4px 8px; }
QMenuBar::item:selected { background-color: #6a6a6a; }
QMenu { background-color: #484848; color: #e0e0e0; border: 1px solid #303030; }
QMenu::item:selected { background-color: #6a6a6a; }
QMenu::separator { height: 1px; background-color: #606060; margin-left: 5px; margin-right: 5px; }
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #606060, stop:1 #505050);
    color: #e0e0e0; border: 1px solid #404040; border-radius: 4px;
    padding: 5px 10px; min-height: 18px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #686868, stop:1 #585858);
    border-color: #505050;
}
QPushButton:pressed { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #484848, stop:1 #585858); }
QPushButton:disabled { background-color: #404040; color: #808080; border-color: #353535; }
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555555;
    border-radius: 3px; padding: 4px;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #0078d7; }
QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled { background-color: #303030; color: #707070; }
QComboBox::drop-down {
    border: none; background-color: #505050; border-top-right-radius: 3px;
    border-bottom-right-radius: 3px; width: 20px;
}
QComboBox::down-arrow { image: url(%(IconPath)s); width: 10px; height: 10px; }
QTableWidget {
    background-color: #383838; color: #d8d8d8; gridline-color: #505050;
    alternate-background-color: #404040; selection-background-color: #0066CC;
    selection-color: #ffffff; border: 1px solid #555555;
}
QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #585858, stop:1 #4d4d4d);
    color: #e0e0e0; padding: 5px; border: 1px solid #404040; border-bottom: 2px solid #383838;
}
QGroupBox {
    border: 1px solid #555555; margin-top: 12px; background-color: transparent; border-radius: 4px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px 0 5px;
    left: 10px; color: #e0e0e0; background-color: #4a4a4a; border-radius: 3px;
}
QStatusBar { background-color: #383838; color: #d0d0d0; border-top: 1px solid #505050; }
QScrollBar:vertical { border: 1px solid #555555; background: #3d3d3d; width: 16px; margin: 0px; }
QScrollBar::handle:vertical { background: #606060; min-height: 25px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: #686868; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { border: 1px solid #555555; background: #3d3d3d; height: 16px; margin: 0px; }
QScrollBar::handle:horizontal { background: #606060; min-width: 25px; border-radius: 3px; }
QScrollBar::handle:horizontal:hover { background: #686868; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QCheckBox { spacing: 5px; }
QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; }
QCheckBox::indicator:unchecked { background-color: #454545; border: 1px solid #555555; }
QCheckBox::indicator:unchecked:hover { border: 1px solid #656565; }
QCheckBox::indicator:checked { background-color: #0078d7; border: 1px solid #005ca8; }
QCheckBox::indicator:checked:hover { background-color: #0088f7; border: 1px solid #006fc8; }
QDateEdit { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555555; border-radius: 3px; }
QDateEdit::drop-down {
    subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
    border-left: 1px solid #555555; background-color: #505050;
    border-top-right-radius: 3px; border-bottom-right-radius: 3px;
}
QDateEdit::down-arrow { image: url(%(IconPath)s); }
QListWidget { background-color: #383838; color: #d8d8d8; border: 1px solid #555555; border-radius: 3px; }
QListWidget::item { padding: 3px; }
QListWidget::item:selected { background-color: #0066CC; color: #ffffff; border-radius: 2px; }
QDialog { background-color: #454545; }
QMessageBox { background-color: #454545; }
QMessageBox QLabel { color: #e0e0e0; }
"""


def apply_theme_globally(application, theme_name):
    global DARK_STYLE_SHEET
    if theme_name == QORONGU_MAVZU_NOMI:
        down_arrow_path = resource_path(os.path.join("resources", "icons", "down_arrow_light.png")).replace("\\", "/")
        formatted_dark_style_sheet = DARK_STYLE_SHEET % {'IconPath': down_arrow_path}
        application.setStyleSheet(formatted_dark_style_sheet)
    else:  # Yorqin mavzu yoki boshqa
        application.setStyleSheet("")  # Standart Qt uslubini tiklash
        application.setPalette(QApplication.style().standardPalette())  # Palitrani ham tiklash


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.column_settings_changed_externally = False  # Ustun sozlamalari tashqaridan o'zgarganini kuzatish

        # Sozlamalarni yuklash (bu APP_SETTINGS ni ham yangilaydi)
        # self.settings obyektini bu yerda ishlatishdan oldin, u mavjudligiga ishonch hosil qilish kerak.
        # load_settings() funksiyasi DEFAULT_SETTINGS.copy() ni qaytarishi mumkin.
        initial_program_settings = load_settings()  # global APP_SETTINGS ni yangilaydi

        # Dastlabki sozlamalarni tekshirish va kerak bo'lsa, standartlarni o'rnatish
        # Bu self.settings atributini yaratmaydi, balki global APP_SETTINGS bilan ishlaydi
        if "theme" not in initial_program_settings:
            set_setting("theme", YORQIN_MAVZU_NOMI)
        if "visible_columns" not in initial_program_settings or not initial_program_settings.get("visible_columns") or \
                "column_headers_uz" not in initial_program_settings or not initial_program_settings.get(
            "column_headers_uz"):
            self._set_default_column_settings_if_needed(force_save=True)
        if "custom_text_fields" not in initial_program_settings:
            set_setting("custom_text_fields", [])

        if not create_tables():
            # Bu yerda QMessageBox ishlatish xavfli, chunki QApplication hali to'liq ishga tushmagan bo'lishi mumkin
            print("KRITIK XATOLIK: Ma'lumotlar bazasini yaratib bo'lmadi. Dastur yopiladi.")
            sys.exit(1)

        self.setWindowTitle("Elektron Omborxona")
        self.setGeometry(100, 100, 1450, 800)
        self.load_icons()
        self.load_column_settings_from_config()  # Sozlamalardan ustunlarni yuklash

        self.init_ui()
        self.table_manager = TableManager(self.table_widget, self.table_headers_db_keys, self.table_display_headers_uz)
        self.connect_signals()
        self.refresh_all_data_and_filters()

    def _set_default_column_settings_if_needed(self, force_save=False):
        """
        Agar 'visible_columns' yoki 'column_headers_uz' sozlamalarda mavjud bo'lmasa yoki bo'sh bo'lsa,
        standart qiymatlarni o'rnatadi.
        Bu metod self.settings ga tayanmaydi, balki get_setting/set_setting orqali ishlaydi.
        """
        default_fields_info = get_all_possible_component_fields_info()

        # visible_columns ni tekshirish
        current_visible = get_setting("visible_columns", [])
        if not current_visible or force_save:
            default_visible_keys = [info['db_key'] for info in default_fields_info if info.get('default_visible', True)]
            set_setting("visible_columns", default_visible_keys)
            if force_save: print("Standart 'visible_columns' o'rnatildi.")

        # column_headers_uz ni tekshirish
        current_headers = get_setting("column_headers_uz", {})
        needs_update_headers = False
        if not current_headers or force_save:  # Agar bo'sh bo'lsa yoki majburiy saqlash
            needs_update_headers = True
        else:  # Agar mavjud bo'lsa, barcha maydonlar uchun sarlavha borligini tekshirish
            for info in default_fields_info:
                if info['db_key'] not in current_headers:
                    needs_update_headers = True
                    break

        if needs_update_headers:
            updated_headers = {}
            for info in default_fields_info:
                # Agar joriy sozlamalarda sarlavha bo'lsa, uni saqlab qolamiz, aks holda standartni olamiz
                updated_headers[info['db_key']] = current_headers.get(info['db_key'], info['display_name_uz'])
            set_setting("column_headers_uz", updated_headers)
            if force_save: print("Standart 'column_headers_uz' o'rnatildi yoki yangilandi.")

    def load_column_settings_from_config(self):
        """
        Sozlamalardan ustun ma'lumotlarini (db_keys, display_headers) yuklaydi.
        Bu metod `self.table_headers_db_keys` va `self.table_display_headers_uz` ni o'rnatadi.
        """
        all_fields_info_list = get_all_possible_component_fields_info()
        all_fields_map = {info['db_key']: info for info in all_fields_info_list}

        # Ko'rinadigan ustunlar (sozlamalardan)
        visible_db_keys_from_settings = get_setting("visible_columns", [])
        if not visible_db_keys_from_settings:  # Agar sozlamalarda bo'sh bo'lsa (nazariy)
            self.table_headers_db_keys = [info['db_key'] for info in all_fields_info_list if
                                          info.get('default_visible', True)]
            # set_setting("visible_columns", self.table_headers_db_keys) # Bu _set_default... da qilinadi
        else:
            # Sozlamalardagi visible_columns haqiqiy mavjud ustunlarga mos kelishini tekshirish
            self.table_headers_db_keys = [key for key in visible_db_keys_from_settings if key in all_fields_map]
            if len(self.table_headers_db_keys) != len(visible_db_keys_from_settings):
                print("OGOHLANTIRISH: Ba'zi 'visible_columns' sozlamalari eskirgan va o'tkazib yuborildi.")
                set_setting("visible_columns", self.table_headers_db_keys)  # Tozalangan ro'yxatni saqlash

        # Sarlavhalar xaritasi (sozlamalardan)
        column_headers_map_uz_from_settings = get_setting("column_headers_uz", {})
        self.column_headers_map_uz = {}  # Bu atributni saqlab qolamiz, ManageColumnsDialog uchun kerak
        for info in all_fields_info_list:
            db_key = info['db_key']
            self.column_headers_map_uz[db_key] = column_headers_map_uz_from_settings.get(db_key,
                                                                                         info['display_name_uz'])

        # Ko'rsatiladigan sarlavhalar ro'yxati (ko'rinadigan ustunlar tartibida)
        self.table_display_headers_uz = []
        for key in self.table_headers_db_keys:
            self.table_display_headers_uz.append(self.column_headers_map_uz.get(key, key.replace("_", " ").title()))

    def load_icons(self):
        self.icons = {name: QIcon(self._get_icon_path(f"{name}.png"))
                      for name in ["plus", "pencil", "delete", "exit", "info",
                                   "settings", "export", "pdf", "refresh",
                                   "label", "www", "project_revision",
                                   "search_advanced", "order_list", "columns",
                                   "table", "template"  # template.png qo'shildi
                                   ]}

    def _get_icon_path(self, filename):
        relative_icon_path = os.path.join("resources", "icons", filename)
        path = resource_path(relative_icon_path)
        if os.path.exists(path):
            return path
        else:
            print(f"OGOHLANTIRISH: Ikona topilmadi - {path}");
            return ""

    def init_ui(self):
        central_widget = QWidget();
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Filtrlar paneli
        top_filter_layout = QHBoxLayout()
        search_groupbox = QGroupBox("Qidiruv");
        search_layout_h = QHBoxLayout(search_groupbox)
        self.search_input = QLineEdit();
        self.search_input.setPlaceholderText("Nomi, qism raqami, loyiha, ishlab chiqaruvchi...")
        search_layout_h.addWidget(self.search_input);
        top_filter_layout.addWidget(search_groupbox, 2)

        cat_filter_groupbox = QGroupBox("Kategoriya");
        cat_filter_layout_h = QHBoxLayout(cat_filter_groupbox)
        self.category_filter_combo = QComboBox();
        self.category_filter_combo.addItem("Barcha kategoriyalar")
        cat_filter_layout_h.addWidget(self.category_filter_combo);
        top_filter_layout.addWidget(cat_filter_groupbox, 1)

        proj_filter_groupbox = QGroupBox("Loyiha");
        proj_filter_layout_h = QHBoxLayout(proj_filter_groupbox)
        self.project_filter_combo = QComboBox();
        self.project_filter_combo.addItem("Barcha loyihalar")
        proj_filter_layout_h.addWidget(self.project_filter_combo);
        top_filter_layout.addWidget(proj_filter_groupbox, 1)

        self.low_stock_checkbox = QCheckBox("Faqat kam qolganlar");
        top_filter_layout.addWidget(self.low_stock_checkbox)
        top_filter_layout.addStretch(1);
        main_layout.addLayout(top_filter_layout)

        # Amallar paneli
        action_button_layout = QHBoxLayout();
        actions_groupbox = QGroupBox("Amallar")
        actions_layout_h = QHBoxLayout(actions_groupbox)

        self.refresh_button = QPushButton(self.icons.get("refresh", QIcon()), " Yangilash")
        actions_layout_h.addWidget(self.refresh_button)

        self.add_custom_field_button = QPushButton(self.icons.get("table", QIcon()), " Maxsus Maydon")
        actions_layout_h.addWidget(self.add_custom_field_button)

        self.add_button = QPushButton(self.icons.get("plus", QIcon()), " Qo'shish");
        actions_layout_h.addWidget(self.add_button)
        self.edit_button = QPushButton(self.icons.get("pencil", QIcon()), " Tahrirlash");
        actions_layout_h.addWidget(self.edit_button)
        self.delete_button = QPushButton(self.icons.get("delete", QIcon()), " O'chirish");
        actions_layout_h.addWidget(self.delete_button)
        self.open_datasheet_button = QPushButton(self.icons.get("pdf", QIcon()), " Datasheet");
        self.open_datasheet_button.setEnabled(False);
        actions_layout_h.addWidget(self.open_datasheet_button)
        self.search_web_button = QPushButton(self.icons.get("www", QIcon()), " Web Qidiruv");
        self.search_web_button.setEnabled(False);
        actions_layout_h.addWidget(self.search_web_button)

        self.label_button = QPushButton(self.icons.get("label", QIcon()), " Etiketka");
        label_menu = QMenu(self)
        generate_label_action = QAction("Tanlangan uchun etiketka...", self);
        generate_label_action.triggered.connect(lambda: generate_label_for_selected(self))
        label_menu.addAction(generate_label_action);
        self.label_button.setMenu(label_menu);
        self.label_button.setEnabled(False);
        actions_layout_h.addWidget(self.label_button)

        self.advanced_search_button = QPushButton(self.icons.get("search_advanced", QIcon()),
                                                  " Kengaytirilgan qidiruv");
        actions_layout_h.addWidget(self.advanced_search_button)
        self.generate_order_list_button = QPushButton(self.icons.get("order_list", QIcon()), " Buyurtma ro'yxati");
        actions_layout_h.addWidget(self.generate_order_list_button)
        self.project_revision_button = QPushButton(self.icons.get("project_revision", QIcon()), " Proyekt Reviziyasi");
        actions_layout_h.addWidget(self.project_revision_button)

        actions_groupbox.setLayout(actions_layout_h);
        action_button_layout.addWidget(actions_groupbox);
        action_button_layout.addStretch(1)
        main_layout.addLayout(action_button_layout)

        # Jadval
        self.table_widget = QTableWidget();
        self.table_widget.verticalHeader().setVisible(False)  # Qator raqamlarini yashirish
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Bir nechta tanlash
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers);  # Ikkita bosishda tahrirlashni o'chirish
        self.table_widget.setSortingEnabled(True)
        main_layout.addWidget(self.table_widget)

        self.setup_menu_and_statusbar()

    def connect_signals(self):
        self.search_input.textChanged.connect(self.apply_filters_and_search)
        self.category_filter_combo.currentTextChanged.connect(self.apply_filters_and_search)
        self.project_filter_combo.currentTextChanged.connect(self.apply_filters_and_search)
        self.low_stock_checkbox.stateChanged.connect(self.apply_filters_and_search)

        self.refresh_button.clicked.connect(self.refresh_all_data_and_filters)
        self.add_custom_field_button.clicked.connect(self.open_manage_custom_fields_dialog)
        self.add_button.clicked.connect(self.open_add_component_dialog)
        self.edit_button.clicked.connect(self.open_edit_component_dialog)
        self.delete_button.clicked.connect(lambda: delete_selected_components(self))
        self.open_datasheet_button.clicked.connect(self.open_selected_datasheet)
        self.search_web_button.clicked.connect(lambda: search_selected_component_online(self))

        self.table_widget.itemDoubleClicked.connect(self.handle_table_double_click)
        self.table_widget.selectionModel().selectionChanged.connect(self.update_action_button_states)

        self.project_revision_button.clicked.connect(lambda: perform_project_revision_action(self))
        self.advanced_search_button.clicked.connect(self.open_advanced_search_dialog)
        self.generate_order_list_button.clicked.connect(self.generate_order_list)

    def setup_menu_and_statusbar(self):
        menu_bar = self.menuBar();
        file_menu = menu_bar.addMenu("&Fayl")

        export_action = QAction(self.icons.get("export", QIcon()), "Eksport qilish...", self);
        export_action.triggered.connect(lambda: export_data_dialog(self))
        file_menu.addAction(export_action)

        extras_menu = file_menu.addMenu("Qo'shimcha imkoniyatlar")
        manage_columns_action = QAction(self.icons.get("columns", QIcon()), "Jadval Ustunlarini Boshqarish...", self)
        manage_columns_action.triggered.connect(self.open_manage_columns_dialog)
        extras_menu.addAction(manage_columns_action)

        # Maxsus Maydonlarni Boshqarish uchun menyu ham qo'shish mumkin (agar tugma yetarli bo'lmasa)
        # manage_custom_fields_menu_action = QAction(self.icons.get("table", QIcon()), "Maxsus Maydonlarni Boshqarish...", self)
        # manage_custom_fields_menu_action.triggered.connect(self.open_manage_custom_fields_dialog)
        # extras_menu.addAction(manage_custom_fields_menu_action)

        settings_action = QAction(self.icons.get("settings", QIcon()), "&Sozlamalar", self);
        settings_action.triggered.connect(self.open_settings_dialog)
        extras_menu.addAction(settings_action)

        manage_templates_action = QAction(self.icons.get("template", QIcon()), "Shablonlarni boshqarish", self)
        manage_templates_action.triggered.connect(self.open_manage_templates_dialog)
        extras_menu.addAction(manage_templates_action)

        file_menu.addSeparator()
        exit_action = QAction(self.icons.get("exit", QIcon()), "&Chiqish", self);
        exit_action.setShortcut("Ctrl+Q");
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        warehouse_menu = menu_bar.addMenu("&Ombor");
        manage_locations_action = QAction("Saqlash joylarini boshqarish", self)  # Bu uchun ham ikona qo'shsa bo'ladi
        manage_locations_action.triggered.connect(self.open_manage_locations_dialog);
        warehouse_menu.addAction(manage_locations_action)

        language_menu = menu_bar.addMenu("&Til");
        lang_uz_action = QAction("O'zbekcha", self);
        lang_uz_action.setCheckable(True);
        lang_uz_action.setChecked(True)  # Hozircha faqat O'zbekcha
        language_menu.addAction(lang_uz_action)

        help_menu = menu_bar.addMenu("&Yordam");
        about_action = QAction(self.icons.get("info", QIcon()), "Dastur &haqida", self)
        about_action.triggered.connect(self.show_about_dialog);
        help_menu.addAction(about_action)

        self.setStatusBar(QStatusBar(self));
        self.statusBar().showMessage("Tayyor")

    def refresh_all_data_and_filters(self):
        # 1. Ustun sozlamalarini qayta yuklash (agar o'zgargan bo'lsa)
        self.load_column_settings_from_config()

        # 2. TableManager ni yangi sarlavhalar bilan yangilash
        if hasattr(self, 'table_manager'):
            self.table_manager.update_headers(self.table_headers_db_keys, self.table_display_headers_uz)

        # 3. Filtr Combo Box'larini yangilash
        self.update_category_filter_combo()
        self.update_project_filter_combo()

        # 4. Jadvaldagi ma'lumotlarni joriy filtrlar bilan qayta yuklash
        self.apply_filters_and_search()

        # 5. Amallar tugmalari holatini yangilash
        self.update_action_button_states()

    def update_category_filter_combo(self):
        current_selection = self.category_filter_combo.currentText();
        self.category_filter_combo.blockSignals(True)
        self.category_filter_combo.clear();
        self.category_filter_combo.addItem("Barcha kategoriyalar")
        try:
            categories = get_all_categories_names();
            self.category_filter_combo.addItems(categories)
        except Exception as e:
            print(f"Kategoriya filtrini yangilashda xato: {e}");
            self.category_filter_combo.addItem("XATO")
        idx = self.category_filter_combo.findText(current_selection)
        if idx != -1:
            self.category_filter_combo.setCurrentIndex(idx)
        else:
            self.category_filter_combo.setCurrentIndex(0)
        self.category_filter_combo.blockSignals(False)

    def update_project_filter_combo(self):
        current_selection = self.project_filter_combo.currentText();
        self.project_filter_combo.blockSignals(True)
        self.project_filter_combo.clear();
        self.project_filter_combo.addItem("Barcha loyihalar")
        try:
            projects = get_distinct_project_names();
            self.project_filter_combo.addItems(projects)
        except Exception as e:
            print(f"Loyiha filtrini yangilashda xato: {e}");
            self.project_filter_combo.addItem("XATO")
        idx = self.project_filter_combo.findText(current_selection)
        if idx != -1:
            self.project_filter_combo.setCurrentIndex(idx)
        else:
            self.project_filter_combo.setCurrentIndex(0)
        self.project_filter_combo.blockSignals(False)

    def get_current_filters(self):
        filters = {'search_text': self.search_input.text().strip().lower(),
                   'category_name': self.category_filter_combo.currentText(),
                   'project_name': self.project_filter_combo.currentText(),
                   'low_stock_only': self.low_stock_checkbox.isChecked()}
        if filters['category_name'] == "Barcha kategoriyalar": filters['category_name'] = None
        if filters['project_name'] == "Barcha loyihalar": filters['project_name'] = None
        return filters

    def apply_filters_and_search(self):
        if not hasattr(self, 'table_manager'): return
        component_count = self.table_manager.load_and_display_data(self.get_current_filters())
        self.statusBar().showMessage(f"{component_count} ta komponent topildi.", 3000)

    def _ask_user_to_select_datasheet(self, paths_string):
        paths = [p.strip() for p in paths_string.split(';') if p.strip()]
        if not paths: return None
        if len(paths) == 1: return paths[0]

        dialog = QDialog(self);
        dialog.setWindowTitle("Datasheet tanlash")
        layout = QVBoxLayout(dialog);
        label = QLabel("Bir nechta datasheet/havola topildi. Ochish uchun birini tanlang:")
        layout.addWidget(label);
        list_widget = QListWidget()
        for path_or_url_item in paths:
            display_text = os.path.basename(path_or_url_item) if os.path.exists(
                path_or_url_item) and not path_or_url_item.startswith(('http://', 'https://')) else path_or_url_item
            list_widget.addItem(display_text)
        list_widget.setCurrentRow(0);
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept);
        buttons.rejected.connect(dialog.reject);
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted and list_widget.currentItem():
            selected_index = list_widget.currentRow();
            return paths[selected_index]
        return None

    def handle_table_double_click(self, item):
        if item and hasattr(self, 'table_headers_db_keys'):  # table_headers_db_keys mavjudligini tekshirish
            current_row = item.row()
            # Datasheet ustunini bosganda
            datasheet_col_idx = -1
            if "datasheet_path" in self.table_headers_db_keys:
                datasheet_col_idx = self.table_headers_db_keys.index("datasheet_path")

            if datasheet_col_idx != -1 and item.column() == datasheet_col_idx:
                datasheet_path_item = self.table_widget.item(current_row, datasheet_col_idx)
                if datasheet_path_item:
                    paths_string = datasheet_path_item.toolTip() or datasheet_path_item.text()  # toolTip da to'liq yo'l
                    if paths_string:
                        path_to_open = self._ask_user_to_select_datasheet(paths_string)
                        if path_to_open: self.open_datasheet(path_to_open); return

            # Agar datasheet ustuni bosilmagan bo'lsa yoki datasheet bo'sh bo'lsa, tahrirlash oynasini ochish
            self.table_widget.selectRow(current_row);  # Qatorni tanlash
            self.open_edit_component_dialog()

    def update_action_button_states(self):
        selected_rows = self.table_widget.selectionModel().selectedRows();
        has_selection = bool(selected_rows)
        enable_single = len(selected_rows) == 1;

        self.edit_button.setEnabled(enable_single)
        self.delete_button.setEnabled(has_selection);
        self.label_button.setEnabled(has_selection)  # Etiketka bir nechta uchun ham bo'lishi mumkin
        self.search_web_button.setEnabled(enable_single)

        enable_datasheet = False
        if enable_single and "datasheet_path" in self.table_headers_db_keys:
            current_row = selected_rows[0].row()
            datasheet_col_idx = self.table_headers_db_keys.index("datasheet_path")
            datasheet_item = self.table_widget.item(current_row, datasheet_col_idx)
            if datasheet_item and (datasheet_item.toolTip() or datasheet_item.text()):
                enable_datasheet = True
        self.open_datasheet_button.setEnabled(enable_datasheet)

    def open_selected_datasheet(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if len(selected_rows) != 1: return  # Faqat bitta tanlangan bo'lsa

        current_row = selected_rows[0].row()
        if "datasheet_path" not in self.table_headers_db_keys:
            QMessageBox.information(self, "Datasheet yo'q", "Datasheet ustuni jadvalda ko'rsatilmagan.");
            return

        datasheet_col_idx = self.table_headers_db_keys.index("datasheet_path")
        datasheet_path_item = self.table_widget.item(current_row, datasheet_col_idx)

        if datasheet_path_item:
            paths_string = datasheet_path_item.toolTip() or datasheet_path_item.text()
            if paths_string:
                path_to_open = self._ask_user_to_select_datasheet(paths_string)
                if path_to_open: self.open_datasheet(path_to_open); return

        QMessageBox.information(self, "Datasheet yo'q",
                                "Tanlangan komponent uchun datasheet ko'rsatilmagan yoki fayl tanlanmadi.")

    def open_datasheet(self, path_or_url):
        if not path_or_url: return

        url_to_open = QUrl(path_or_url)
        if not url_to_open.scheme():  # Agar scheme yo'q bo'lsa (masalan, http, file)
            if os.path.exists(path_or_url):  # Mahalliy faylmi?
                url_to_open = QUrl.fromLocalFile(path_or_url)
            elif "." in path_or_url and not path_or_url.startswith(("/", "\\")):  # Ehtimol, http:// siz yozilgan URL
                url_to_open = QUrl("http://" + path_or_url, QUrl.TolerantMode)
            else:  # Noma'lum format
                QMessageBox.warning(self, "Xatolik", f"'{path_or_url}' fayli topilmadi yoki URL manzili noto'g'ri.");
                return

        if not QDesktopServices.openUrl(url_to_open):
            QMessageBox.warning(self, "Xatolik", f"'{path_or_url}' manzilini ochib bo'lmadi.")

    def open_add_component_dialog(self):
        dialog = AddComponentDialog(self)  # parent=self
        if dialog.check_initialization_error():
            print("XATOLIK: AddComponentDialog ni ochishda muammo.");
            return

        if dialog.exec_() == QDialog.Accepted:
            data_from_dialog = dialog.get_data_from_fields()
            new_component_id = add_component(data_from_dialog)
            if new_component_id:
                self.statusBar().showMessage(f"'{data_from_dialog['name']}' (ID: {new_component_id}) qo'shildi.", 5000)
                self.refresh_all_data_and_filters()
            else:
                QMessageBox.critical(self, "Xatolik",
                                     f"'{data_from_dialog.get('name', 'N/A')}' komponentini qo'shishda xatolik.")
        else:
            self.statusBar().showMessage("Qo'shish bekor qilindi.", 3000)

    def open_edit_component_dialog(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Xatolik", "Tahrirlash uchun bitta komponent tanlang!");
            return

        current_row_display = selected_rows[0].row()
        if "id" not in self.table_headers_db_keys:
            QMessageBox.critical(self, "Xatolik", "ID ustuni jadvalda ko'rsatilmagan. Tahrirlash mumkin emas.");
            return

        id_col_index_in_display = self.table_headers_db_keys.index("id")
        try:
            id_item = self.table_widget.item(current_row_display, id_col_index_in_display)
            if id_item is None: raise ValueError("ID katakchasi bo'sh (None).")
            component_id_to_edit = int(id_item.text())
        except (AttributeError, ValueError, TypeError) as e:
            print(f"XATOLIK: IDni olishda: {e}");
            QMessageBox.critical(self, "Xatolik", f"Tanlangan IDni o'qishda xato: {e}");
            return

        dialog = AddComponentDialog(self, component_id_to_edit=component_id_to_edit)  # parent=self
        if dialog.check_initialization_error(): return

        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data_from_fields()
            if update_component(component_id_to_edit, updated_data):
                self.statusBar().showMessage(
                    f"'{updated_data.get('name', 'N/A')}' (ID: {component_id_to_edit}) yangilandi.", 5000)
                self.refresh_all_data_and_filters()
            else:
                QMessageBox.critical(self, "Xatolik",
                                     f"'{updated_data.get('name', 'N/A')}' komponentini yangilashda xatolik.")
        else:
            self.statusBar().showMessage("Tahrirlash bekor qilindi.", 3000)

    def show_about_dialog(self):
        QMessageBox.about(self, "Dastur haqida",
                          f"<b>Elektron Omborxona</b><br>Versiya: 0.8.1<br>Yaratuvchi: Abdulloh<br>Python {sys.version_info.major}.{sys.version_info.minor}, PyQt5")

    def open_settings_dialog(self):
        old_theme = get_setting("theme");  # Joriy mavzuni olish
        dialog = SettingsDialog(self, available_themes=[YORQIN_MAVZU_NOMI, QORONGU_MAVZU_NOMI])

        if dialog.exec_() == QDialog.Accepted:
            # Sozlamalar SettingsDialog ichida `set_setting` orqali saqlanadi.
            # Bu yerda faqat mavzu o'zgargan bo'lsa, uni qo'llash kerak.
            new_theme = get_setting("theme")  # Yangilangan mavzuni olish
            if old_theme != new_theme:
                QMessageBox.information(self, "Mavzu o'zgarishi",
                                        "Interfeys mavzusi o'zgarishi uchun dasturni qayta ishga tushiring.")
                apply_theme_globally(QApplication.instance(), new_theme)
        else:  # Agar bekor qilinsa, eski mavzuni qayta qo'llash (agar SettingsDialog uni vaqtincha o'zgartirgan bo'lsa)
            apply_theme_globally(QApplication.instance(), old_theme)

    def open_manage_locations_dialog(self):
        dialog = ManageLocationsDialog(self);
        dialog.exec_();
        self.refresh_all_data_and_filters()  # Joylar o'zgargan bo'lishi mumkin

    def open_advanced_search_dialog(self):
        try:
            from ui.advanced_search_dialog import AdvancedSearchDialog  # Lazy import
        except ImportError as e:
            QMessageBox.critical(self, "Import Xatosi", f"Kengaytirilgan qidiruv dialogini yuklab bo'lmadi: {e}");
            return

        dialog = AdvancedSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            adv_filters = dialog.get_filters()
            if adv_filters:
                self.search_input.blockSignals(True);
                self.search_input.clear();
                self.search_input.blockSignals(False)

                # Asosiy filtr ComboBox'larini "Barcha..." holatiga qaytarish, agar kengaytirilgan filtrda
                # ular uchun qiymat berilgan bo'lsa.
                if 'category_name' in adv_filters:
                    self.category_filter_combo.blockSignals(True);
                    idx_cat = self.category_filter_combo.findText("Barcha kategoriyalar")
                    if idx_cat != -1: self.category_filter_combo.setCurrentIndex(idx_cat)
                    self.category_filter_combo.blockSignals(False)

                if 'project_name' in adv_filters:
                    self.project_filter_combo.blockSignals(True);
                    idx_proj = self.project_filter_combo.findText("Barcha loyihalar")
                    if idx_proj != -1: self.project_filter_combo.setCurrentIndex(idx_proj)
                    self.project_filter_combo.blockSignals(False)

                if 'low_stock_only' in adv_filters:  # Bu checkbox holatini to'g'ridan-to'g'ri o'rnatadi
                    self.low_stock_checkbox.blockSignals(True);
                    self.low_stock_checkbox.setChecked(adv_filters['low_stock_only']);
                    self.low_stock_checkbox.blockSignals(False)

                # Asosiy filtrlar qiymatlarini olish (ular kengaytirilgan qidiruvda o'zgartirilmagan bo'lishi mumkin)
                current_main_filters = self.get_current_filters();
                # Kengaytirilgan qidiruv filtrlarini asosiy filtrlar bilan birlashtirish
                final_filters = {**current_main_filters, **adv_filters}

                # Agar kengaytirilgan qidiruvda nom, qism raqami va hk bo'yicha qidiruv bo'lsa,
                # asosiy qidiruv maydonini (search_text) hisobga olmaslik
                if 'adv_name' in final_filters or 'adv_part_number' in final_filters or \
                        'adv_value' in final_filters or 'adv_manufacturer' in final_filters:
                    final_filters.pop('search_text', None)

                if hasattr(self, 'table_manager'):
                    count = self.table_manager.load_and_display_data(final_filters)
                    self.statusBar().showMessage(f"{count} ta komponent (kengaytirilgan) topildi.", 3000)
            else:  # Agar kengaytirilgan qidiruvda hech qanday filtr tanlanmagan bo'lsa
                self.refresh_all_data_and_filters()  # Oddiy qidiruvga qaytish

    def generate_order_list(self):
        generate_order_list_action(self)

    def open_manage_templates_dialog(self):
        QMessageBox.information(self, "Ishlab chiqilmoqda", "Shablonlarni boshqarish ishlab chiqilmoqda.")

    def apply_theme_from_main(self, application_instance, theme_name):
        # Bu metod SettingsDialog dan chaqirilishi mumkin (Apply tugmasi bosilganda)
        apply_theme_globally(application_instance, theme_name)

    def open_manage_columns_dialog(self):
        # Eng so'nggi maydonlar ro'yxatini olish (barcha standart va maxsus)
        all_fields_info_latest = get_all_possible_component_fields_info()

        # Joriy ko'rinadigan kalitlar va sarlavhalar self.load_column_settings_from_config() da o'rnatilgan
        dialog = ManageColumnsDialog(self,
                                     all_fields_info_initial=all_fields_info_latest,
                                     current_visible_keys=list(self.table_headers_db_keys),
                                     current_headers_map_uz=dict(self.column_headers_map_uz))

        if dialog.exec_() == QDialog.Accepted:
            # Dialogdan yangilangan (va ehtimol o'chirilgan maxsus ustunlar bilan) sozlamalarni olish
            new_visible_keys, new_headers_map_uz = dialog.new_visible_keys_on_accept, dialog.new_headers_map_uz_on_accept

            set_setting("visible_columns", new_visible_keys)

            # column_headers_uz ni yangilash. new_headers_map_uz faqat list_widget da qolganlar uchun sarlavhalarni o'z ichiga oladi.
            # Biz barcha mavjud maydonlar uchun sarlavhalarni saqlashimiz kerak.
            final_headers_to_save = {}
            all_current_fields_after_dialog = get_all_possible_component_fields_info()  # Bu endi o'chirilganlarni o'z ichiga olmaydi

            for field in all_current_fields_after_dialog:
                db_key = field['db_key']
                # Agar dialogdan sarlavha kelgan bo'lsa (ya'ni u dialogda ko'rsatilgan bo'lsa), uni ishlatamiz.
                # Aks holda (nazariy jihatdan bu holat bo'lmasligi kerak, chunki new_headers_map_uz barcha qolganlarni qamrab oladi),
                # standart sarlavhani olamiz.
                final_headers_to_save[db_key] = new_headers_map_uz.get(db_key, field['display_name_uz'])

            set_setting("column_headers_uz", final_headers_to_save)

            QMessageBox.information(self, "Ustunlar Yangilandi",
                                    "Jadval ustunlari muvaffaqiyatli yangilandi." +
                                    (
                                        "\nO'zgarishlar to'liq kuchga kirishi uchun dasturni qayta ishga tushirish tavsiya etiladi."
                                        if self.column_settings_changed_externally else "")
                                    )
            self.column_settings_changed_externally = False  # Bayroqni tozalash
            self.refresh_all_data_and_filters()
        else:  # Agar bekor qilinsa
            if self.column_settings_changed_externally:
                QMessageBox.information(self, "Diqqat",
                                        "Ustunlar sozlamalari o'zgartirilgan bo'lishi mumkin (maxsus ustun o'chirilgan bo'lishi mumkin).\n"
                                        "O'zgarishlar to'liq kuchga kirishi uchun dasturni qayta ishga tushirish tavsiya etiladi.")
                self.column_settings_changed_externally = False
                self.refresh_all_data_and_filters()  # Har ehtimolga qarshi

    def open_manage_custom_fields_dialog(self):
        dialog = ManageCustomFieldsDialog(self)  # parent=self
        # Dialog.exec_() bloking chaqiruv, shuning uchun u yopilguncha kod shu yerda to'xtaydi
        if dialog.exec_() == QDialog.Accepted:
            # Agar ManageCustomFieldsDialog da OK bosilsa va `settings_changed_in_dialog` true bo'lsa
            if hasattr(dialog, 'settings_changed_in_dialog') and dialog.settings_changed_in_dialog:
                QMessageBox.information(self, "Maxsus Maydonlar",
                                        "Maxsus maydonlar sozlamalari yangilandi.\nO'zgarishlar to'liq kuchga kirishi uchun dasturni qayta ishga tushirish tavsiya etiladi.")
                self.refresh_all_data_and_filters()
        # Agar Cancel bosilsa yoki o'zgarish bo'lmasa, hech narsa qilmaymiz,
        # lekin ManageColumnsDialog uchun `column_settings_changed_externally` bayrog'i
        # ManageCustomFieldsDialog orqali ham o'rnatilishi mumkin.
        if self.column_settings_changed_externally:  # Agar ManageCustomFieldsDialog ManageColumnsDialog ga ta'sir qilgan bo'lsa
            self.refresh_all_data_and_filters()
            self.column_settings_changed_externally = False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Dastlabki sozlamalarni yuklash va mavzuni qo'llash
    # Bu yerda `load_settings` global `APP_SETTINGS` ni o'rnatadi
    app_initial_settings = load_settings()
    apply_theme_globally(app, app_initial_settings.get("theme", YORQIN_MAVZU_NOMI))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())