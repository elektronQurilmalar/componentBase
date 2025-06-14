# ElektronKomponentlarUchoti/ui/manage_locations_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QMessageBox, QAbstractItemView, QLabel, QLineEdit,
                             QDialogButtonBox)  # QDialogButtonBox qo'shildi
from PyQt5.QtCore import Qt

try:
    from app_logic.db_manager import (get_all_storage_locations_names,
                                      add_storage_location_db,
                                      delete_storage_location_db)
except ImportError:
    print("XATOLIK: db_manager.py topilmadi yoki import qilishda muammo.")


    def get_all_storage_locations_names():
        return ["Xato: Joylar yuklanmadi"]


    def add_storage_location_db(name):
        print("MB XATOSI: Joy qo'shilmadi"); return False


    def delete_storage_location_db(name):
        print("MB XATOSI: Joy o'chirilmadi"); return False


class ManageLocationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Saqlash Joylarini Boshqarish")
        self.setMinimumWidth(400)
        self.setModal(True)

        self.main_layout = QVBoxLayout(self)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Yangi joy nomi:"))
        self.new_location_input = QLineEdit()
        self.new_location_input.setPlaceholderText("Masalan, Polka Z9")
        add_layout.addWidget(self.new_location_input)
        self.add_new_button = QPushButton("Qo'shish")
        self.add_new_button.clicked.connect(self.add_new_location_from_input)
        add_layout.addWidget(self.add_new_button)
        self.main_layout.addLayout(add_layout)

        self.locations_list_widget = QListWidget()
        self.locations_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_list()
        self.main_layout.addWidget(self.locations_list_widget)

        self.button_box = QDialogButtonBox()  # Standard tugmalar uchun
        self.delete_button = self.button_box.addButton("Tanlanganni o'chirish", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton("Yopish", QDialogButtonBox.AcceptRole)  # AcceptRole yopish uchun

        self.delete_button.clicked.connect(self.delete_selected_location)
        self.close_button.clicked.connect(self.accept)  # Dialog yopiladi
        self.main_layout.addWidget(self.button_box)

    def populate_list(self):
        self.locations_list_widget.clear()
        self.locations_list_widget.addItems(get_all_storage_locations_names())

    def add_new_location_from_input(self):
        new_location_text = self.new_location_input.text().strip()
        if not new_location_text:
            QMessageBox.warning(self, "Bo'sh nom", "Saqlash joyi nomi bo'sh bo'lishi mumkin emas.")
            return

        existing_locations_lower = [loc.lower() for loc in get_all_storage_locations_names()]
        if new_location_text.lower() in existing_locations_lower:
            QMessageBox.information(self, "Mavjud", f"'{new_location_text}' saqlash joyi allaqachon mavjud.")
            self.new_location_input.clear()
            return

        if add_storage_location_db(new_location_text):
            self.populate_list()
            self.new_location_input.clear()
            items = self.locations_list_widget.findItems(new_location_text, Qt.MatchExactly)
            if items: self.locations_list_widget.setCurrentItem(items[0])
        else:
            QMessageBox.warning(self, "Xatolik",
                                f"'{new_location_text}' saqlash joyini bazaga qo'shib bo'lmadi. Ehtimol, allaqachon mavjud yoki MB xatosi.")

    def delete_selected_location(self):
        selected_items = self.locations_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Tanlanmagan", "O'chirish uchun avval saqlash joyini tanlang.")
            return

        location_to_delete = selected_items[0].text()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Tasdiqlash")
        msg_box.setText(f"Haqiqatdan ham '{location_to_delete}' saqlash joyini o'chirmoqchimisiz?\n"
                        f"Agar bu joy biror komponentda ishlatilayotgan bo'lsa, o'chirilmaydi.")
        yes_button = msg_box.addButton("Ha", QMessageBox.YesRole)
        no_button = msg_box.addButton("Yo'q", QMessageBox.NoRole)
        msg_box.setDefaultButton(no_button)
        msg_box.exec_()

        if msg_box.clickedButton() == yes_button:
            if delete_storage_location_db(location_to_delete):
                self.populate_list()
            else:
                QMessageBox.warning(self, "Xatolik",
                                    f"'{location_to_delete}' saqlash joyini o'chirib bo'lmadi.\n"
                                    "Ehtimol, bu joy biror komponentda ishlatilmoqda yoki bazada topilmadi.")