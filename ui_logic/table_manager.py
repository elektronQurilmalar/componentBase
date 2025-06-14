# ElektronKomponentlarUchoti/ui_logic/table_manager.py
import os
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class TableManager:
    def __init__(self, table_widget, headers_db_keys, display_headers_uz):
        self.table_widget = table_widget
        self.headers_db_keys = list(headers_db_keys)  # Nusxasini olish
        self.display_headers_uz = list(display_headers_uz)  # Nusxasini olish
        self.low_stock_color = QColor(180, 100, 100, 150)  # R, G, B, Alpha (yarim shaffof)

    def update_headers(self, new_headers_db_keys, new_display_headers_uz):
        self.headers_db_keys = list(new_headers_db_keys)
        self.display_headers_uz = list(new_display_headers_uz)

    def _parse_value(self, value_str):
        if value_str is None: return None, None
        value_str = str(value_str).strip().lower()
        num_part = ""
        unit_part = ""
        for char in value_str:
            if char.isdigit() or char == '.':
                num_part += char
            else:
                unit_part += char
        try:
            return float(num_part) if num_part else None, unit_part.strip()
        except ValueError:
            return None, value_str

    def load_and_display_data(self, filters=None):
        from app_logic.db_manager import get_all_components

        db_filters = filters.copy() if filters else {}
        components_from_db = get_all_components(db_filters)

        self.populate_table(components_from_db)
        return len(components_from_db)

    def populate_table(self, components_list_of_dicts):
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0)

        if not self.headers_db_keys or not self.display_headers_uz:
            print("OGOHLANTIRISH: Jadval ustunlari aniqlanmagan. Ma'lumotlar ko'rsatilmaydi.")
            self.table_widget.setColumnCount(0)
            return

        self.table_widget.setColumnCount(len(self.display_headers_uz))
        self.table_widget.setHorizontalHeaderLabels(self.display_headers_uz)
        header = self.table_widget.horizontalHeader()

        # Ustun indekslarini bir marta olish
        qty_col_db_key = "quantity"
        desc_col_db_key = "description"
        reminder_text_col_db_key = "reminder_text"
        datasheet_col_db_key = "datasheet_path"
        id_col_db_key = "id"
        min_qty_col_db_key = "min_quantity"
        reminder_date_col_db_key = "reminder_date"
        name_col_db_key = "name"
        part_num_col_db_key = "part_number"
        project_col_db_key = "project"

        for i, db_key in enumerate(self.headers_db_keys):
            # Har bir ustun uchun kenglikni sozlash
            # Bu qismni yanada moslashuvchan qilish mumkin (masalan, sozlamalardan kengliklarni olish)
            if db_key == desc_col_db_key or db_key == reminder_text_col_db_key:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif db_key == datasheet_col_db_key:
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_widget.setColumnWidth(i, 120)
            elif db_key in [id_col_db_key, qty_col_db_key, min_qty_col_db_key, reminder_date_col_db_key]:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                default_width = 110
                if db_key == name_col_db_key:
                    default_width = 150
                elif db_key == part_num_col_db_key:
                    default_width = 130
                elif db_key == project_col_db_key:
                    default_width = 100
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_widget.setColumnWidth(i, default_width)

        for row_idx, component_dict in enumerate(components_list_of_dicts):
            self.table_widget.insertRow(row_idx)
            is_low_stock = False
            min_qty_val = 0
            try:
                current_qty = int(component_dict.get(qty_col_db_key, 0)) if component_dict.get(
                    qty_col_db_key) is not None else 0
                min_qty_val = int(component_dict.get(min_qty_col_db_key, 0)) if component_dict.get(
                    min_qty_col_db_key) is not None else 0
                if min_qty_val > 0 and current_qty <= min_qty_val:
                    is_low_stock = True
            except (ValueError, TypeError):
                pass

            for col_idx, db_key in enumerate(self.headers_db_keys):
                cell_data = component_dict.get(db_key, "")
                item = QTableWidgetItem()

                if db_key in [id_col_db_key, qty_col_db_key, min_qty_col_db_key]:
                    try:
                        val = int(cell_data) if cell_data is not None and str(cell_data).strip() != "" else 0
                        item.setData(Qt.DisplayRole, val)
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    except (ValueError, TypeError):
                        item.setText(str(cell_data) if cell_data is not None else "")
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                elif db_key == datasheet_col_db_key and cell_data:
                    first_path = str(cell_data).split(';')[0].strip()
                    item.setText(os.path.basename(first_path) if first_path else "")
                    item.setToolTip(str(cell_data))
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setText(str(cell_data) if cell_data is not None else "")
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if is_low_stock:
                    item.setBackground(self.low_stock_color)

                if is_low_stock and db_key == qty_col_db_key:
                    item.setToolTip(f"Minimal miqdor ({min_qty_val}) dan kam yoki teng!")

                self.table_widget.setItem(row_idx, col_idx, item)

        self.table_widget.setSortingEnabled(True)