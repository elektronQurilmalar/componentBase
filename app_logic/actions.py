# ElektronKomponentlarUchoti/app_logic/actions.py
import os
import csv
import pandas as pd
import webbrowser
import urllib.parse
from PyQt5.QtWidgets import (QApplication, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QHBoxLayout, QDialogButtonBox, QLabel,
                             QProgressDialog, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer

from .db_manager import delete_component, get_all_components, get_component_by_id, \
    get_all_possible_component_fields_info
from utils.config_manager import get_setting, set_setting


def delete_selected_components(main_window_instance):
    table_widget = main_window_instance.table_widget
    selected_rows = table_widget.selectionModel().selectedRows()
    if not selected_rows: QMessageBox.warning(main_window_instance, "Xatolik",
                                              "O'chirish uchun komponent(lar) tanlang!"); return
    ids_to_delete = [];
    names_to_delete = []
    try:
        id_col_idx_display = main_window_instance.table_headers_db_keys.index('id')
        name_col_idx_display = main_window_instance.table_headers_db_keys.index('name')
    except ValueError:
        QMessageBox.critical(main_window_instance, "Xatolik",
                             "'ID' yoki 'Nomi' ustuni jadvalda topilmadi. O'chirish mumkin emas."); return
    for model_index in selected_rows:
        row = model_index.row()
        try:
            id_item = table_widget.item(row, id_col_idx_display);
            name_item = table_widget.item(row, name_col_idx_display)
            if id_item and name_item:
                ids_to_delete.append(int(id_item.text())); names_to_delete.append(name_item.text())
            else:
                raise ValueError("ID yoki Nomi katakchasi bo'sh.")
        except (AttributeError, ValueError, TypeError) as e:
            QMessageBox.warning(main_window_instance, "Xatolik",
                                f"{row + 1}-qatordagi ID/Nomni o'qib bo'lmadi: {e}"); return
    if not ids_to_delete: return
    confirm_delete_setting = get_setting("confirm_delete", True);
    reply = QMessageBox.Yes
    if confirm_delete_setting:
        msg_box = QMessageBox(main_window_instance);
        msg_box.setIcon(QMessageBox.Question);
        msg_box.setWindowTitle("Tasdiqlash")
        msg_box.setText(
            f"{len(ids_to_delete)} ta komponentni o'chirmoqchimisiz?\n({', '.join(names_to_delete[:5])}{'...' if len(names_to_delete) > 5 else ''})")
        yes_button = msg_box.addButton("Ha", QMessageBox.YesRole);
        no_button = msg_box.addButton("Yo'q", QMessageBox.NoRole)
        msg_box.setDefaultButton(no_button);
        msg_box.exec_();
        reply_button = msg_box.clickedButton()
        if reply_button != yes_button: main_window_instance.statusBar().showMessage("O'chirish bekor qilindi.",
                                                                                    3000); return
    deleted_count = 0;
    error_count = 0
    for comp_id in ids_to_delete:
        if delete_component(comp_id):
            deleted_count += 1
        else:
            error_count += 1
    main_window_instance.statusBar().showMessage(f"{deleted_count} ta o'chirildi, {error_count} ta xatolik.", 5000)
    main_window_instance.refresh_all_data_and_filters()


def search_selected_component_online(main_window_instance):
    table_widget = main_window_instance.table_widget;
    selected_rows = table_widget.selectionModel().selectedRows()
    if len(selected_rows) != 1: QMessageBox.warning(main_window_instance, "Tanlanmagan",
                                                    "Qidirish uchun bitta komponent tanlang!"); return
    current_row = selected_rows[0].row();
    search_terms = []
    try:
        name_idx = main_window_instance.table_headers_db_keys.index(
            'name') if 'name' in main_window_instance.table_headers_db_keys else -1
        part_num_idx = main_window_instance.table_headers_db_keys.index(
            'part_number') if 'part_number' in main_window_instance.table_headers_db_keys else -1
        value_idx = main_window_instance.table_headers_db_keys.index(
            'value') if 'value' in main_window_instance.table_headers_db_keys else -1
        package_idx = main_window_instance.table_headers_db_keys.index(
            'package_type_name') if 'package_type_name' in main_window_instance.table_headers_db_keys else -1
        part_num = table_widget.item(current_row,
                                     part_num_idx).text().strip() if part_num_idx != -1 and table_widget.item(
            current_row, part_num_idx) else ""
        name = table_widget.item(current_row, name_idx).text().strip() if name_idx != -1 and table_widget.item(
            current_row, name_idx) else ""
        if not part_num and not name: QMessageBox.warning(main_window_instance, "Ma'lumot yetarli emas",
                                                          "Komponent nomi yoki qism raqami yo'q (yoki jadvalda ko'rsatilmagan)."); return
        if part_num:
            search_terms.append(part_num)
        elif name:
            search_terms.append(name)
        if value_idx != -1 and table_widget.item(current_row, value_idx):
            value = table_widget.item(current_row, value_idx).text().strip()
            if value and value != '-': search_terms.append(value)
        if package_idx != -1 and table_widget.item(current_row, package_idx):
            package = table_widget.item(current_row, package_idx).text().strip()
            if package and package.lower() not in ['boshqa', 'n/a', '']: search_terms.append(package)
    except (AttributeError, ValueError, IndexError, TypeError) as e:
        QMessageBox.critical(main_window_instance, "Xatolik", f"Qidiruv uchun ma'lumot olishda xato: {e}"); return
    if search_terms:
        full_search_query = " ".join(search_terms);
        query = urllib.parse.quote_plus(full_search_query)
        url = f"https://www.google.com/search?q={query}"
        try:
            webbrowser.open(url); main_window_instance.statusBar().showMessage(
                f"'{full_search_query}' uchun qidirilmoqda...", 3000)
        except Exception as e_web:
            QMessageBox.critical(main_window_instance, "Xatolik", f"Brauzerni ochishda xatolik: {e_web}")


def export_data_dialog(main_window_instance):
    export_db_keys = main_window_instance.table_headers_db_keys;
    headers_for_export = main_window_instance.table_display_headers_uz
    if not export_db_keys: QMessageBox.warning(main_window_instance, "Eksport xatosi",
                                               "Eksport uchun ustunlar tanlanmagan."); return
    current_filters = main_window_instance.get_current_filters();
    components_to_export_dicts = get_all_components(current_filters)
    if not components_to_export_dicts: QMessageBox.warning(main_window_instance, "Eksport xatosi",
                                                           "Joriy filtrlar bo'yicha eksport uchun ma'lumotlar topilmadi."); return
    data_to_export = []
    for comp_dict in components_to_export_dicts: row_data = [comp_dict.get(key, "") for key in
                                                             export_db_keys]; data_to_export.append(row_data)
    options = QFileDialog.Options();
    last_export_dir = get_setting("last_export_dir", os.path.expanduser("~"))
    file_path, selected_filter = QFileDialog.getSaveFileName(main_window_instance, "Ma'lumotlarni eksport qilish",
                                                             os.path.join(last_export_dir, "komponentlar_hisoboti"),
                                                             "Excel fayllari (*.xlsx);;CSV fayllari (*.csv)",
                                                             options=options)
    if file_path:
        set_setting("last_export_dir", os.path.dirname(file_path));
        default_excel_ext = ".xlsx";
        default_csv_ext = ".csv"
        try:
            if selected_filter.startswith("Excel"):
                if not file_path.lower().endswith(default_excel_ext): file_path += default_excel_ext
                _export_to_excel(main_window_instance, file_path, data_to_export, headers_for_export)
            elif selected_filter.startswith("CSV"):
                if not file_path.lower().endswith(default_csv_ext): file_path += default_csv_ext
                _export_to_csv(main_window_instance, file_path, data_to_export, headers_for_export)
            elif file_path.lower().endswith(default_excel_ext):
                _export_to_excel(main_window_instance, file_path, data_to_export, headers_for_export)
            elif file_path.lower().endswith(default_csv_ext):
                _export_to_csv(main_window_instance, file_path, data_to_export, headers_for_export)
            else:
                if not file_path.lower().endswith(default_excel_ext): file_path += default_excel_ext
                _export_to_excel(main_window_instance, file_path, data_to_export, headers_for_export)
        except Exception as e:
            QMessageBox.critical(main_window_instance, "Eksport xatosi", f"Eksport qilishda kutilmagan xatolik:\n{e}")


def _export_to_excel(main_window_instance, file_path, data, headers):
    try:
        df = pd.DataFrame(data, columns=headers);
        df.to_excel(file_path, index=False, engine='openpyxl')
        main_window_instance.statusBar().showMessage(f"'{os.path.basename(file_path)}' ga eksport qilindi.", 5000)
        QMessageBox.information(main_window_instance, "Eksport Muvaffaqiyatli",
                                f"Ma'lumotlar '{file_path}' fayliga saqlandi.")
    except Exception as e:
        QMessageBox.critical(main_window_instance, "Excel Eksport Xatosi", f"Xatolik:\n{e}")


def _export_to_csv(main_window_instance, file_path, data, headers):
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';');
            writer.writerow(headers);
            writer.writerows(data)
        main_window_instance.statusBar().showMessage(f"'{os.path.basename(file_path)}' ga eksport qilindi.", 5000)
        QMessageBox.information(main_window_instance, "Eksport Muvaffaqiyatli",
                                f"Ma'lumotlar '{file_path}' fayliga saqlandi.")
    except Exception as e:
        QMessageBox.critical(main_window_instance, "CSV Eksport Xatosi", f"Xatolik:\n{e}")


def generate_label_for_selected(main_window_instance):
    table_widget = main_window_instance.table_widget;
    selected_rows_indices = table_widget.selectionModel().selectedRows()
    if not selected_rows_indices: QMessageBox.warning(main_window_instance, "Tanlanmagan",
                                                      "Etiketka uchun komponent(lar) tanlang."); return
    label_texts = [];
    db_keys_in_table = main_window_instance.table_headers_db_keys
    for model_index in selected_rows_indices:
        row = model_index.row();
        comp_data = {}
        for i, key in enumerate(db_keys_in_table):
            item = table_widget.item(row, i)
            if key == "datasheet_path" and item:
                comp_data[key] = item.toolTip() if item.toolTip() else item.text()
            else:
                comp_data[key] = item.text() if item else ""
        label_text = f"** {comp_data.get('name', 'N/A')} **\n"
        if comp_data.get('part_number'): label_text += f"Qism №: {comp_data['part_number']}\n"
        if comp_data.get('value'): label_text += f"Qiymat: {comp_data['value']}\n"
        if comp_data.get('package_type_name'): label_text += f"Korpus: {comp_data['package_type_name']}\n"
        if comp_data.get('location_name'): label_text += f"Joy: {comp_data['location_name']}\n"
        if 'id' in comp_data: label_text += f"ID: {comp_data.get('id', 'N/A')}"
        label_texts.append(label_text)
    if label_texts:
        full_label_content = "\n\n---\n\n".join(label_texts);
        msg_box = QMessageBox(main_window_instance)
        msg_box.setWindowTitle("Generatsiya qilingan Etiketkalar");
        msg_box.setText("Quyidagi etiketka(lar) generatsiya qilindi:")
        msg_box.setDetailedText(full_label_content);
        msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse);
        msg_box.setIcon(QMessageBox.Information)
        ok_button = msg_box.addButton("OK", QMessageBox.AcceptRole);
        save_button = msg_box.addButton("Faylga saqlash...", QMessageBox.SaveRole)
        msg_box.setDefaultButton(ok_button);
        msg_box.exec_()
        if msg_box.clickedButton() == save_button: _save_labels_to_file(main_window_instance, full_label_content)


def _save_labels_to_file(main_window_instance, content):
    options = QFileDialog.Options();
    last_export_dir = get_setting("last_export_dir", os.path.expanduser("~"))
    file_path, _ = QFileDialog.getSaveFileName(main_window_instance, "Etiketkalarni faylga saqlash",
                                               os.path.join(last_export_dir, "etiketkalar.txt"),
                                               "Matnli fayllar (*.txt);;Barcha fayllar (*)", options=options)
    if file_path:
        set_setting("last_export_dir", os.path.dirname(file_path))
        try:
            if not file_path.lower().endswith(".txt"): file_path += ".txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(main_window_instance, "Muvaffaqiyatli", f"Etiketkalar '{file_path}' ga saqlandi.")
        except Exception as e:
            QMessageBox.critical(main_window_instance, "Xatolik", f"Faylga saqlashda xatolik:\n{e}")


class GenerateOrderListDialog(QDialog):
    def __init__(self, parent=None, low_stock_components=None):
        super().__init__(parent);
        self.setWindowTitle("Buyurtma uchun ro'yxat (Ombor uchun)");
        self.setMinimumSize(850, 500);
        self.main_window = parent
        layout = QVBoxLayout(self);
        self.table_widget = QTableWidget();
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels(
            ["Nomi", "Qism Raqami", "Kategoriya", "Qiymati", "Korpus", "Omborda", "Min. Miqdor",
             "Buyurtma qilish kerak"])
        layout.addWidget(self.table_widget);
        self.populate_table(low_stock_components);
        button_box = QDialogButtonBox()
        close_button = button_box.addButton("Yopish", QDialogButtonBox.RejectRole);
        export_button = button_box.addButton("CSV ga eksport", QDialogButtonBox.AcceptRole)
        button_box.rejected.connect(self.reject);
        export_button.clicked.connect(self.export_to_csv);
        layout.addWidget(button_box)

    def populate_table(self, low_stock_components):
        self.table_widget.setSortingEnabled(False);
        self.table_widget.setRowCount(0)
        if not low_stock_components: return
        for comp_data in low_stock_components:
            to_order_val = max(0, int(comp_data.get('min_quantity', 0)) - int(comp_data.get('quantity', 0)))
            if to_order_val <= 0: continue
            row_position = self.table_widget.rowCount();
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem(comp_data.get('name')));
            self.table_widget.setItem(row_position, 1, QTableWidgetItem(comp_data.get('part_number')))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem(comp_data.get('category_name')));
            self.table_widget.setItem(row_position, 3, QTableWidgetItem(comp_data.get('value')))
            self.table_widget.setItem(row_position, 4, QTableWidgetItem(comp_data.get('package_type_name')))
            qty_item = QTableWidgetItem();
            qty_item.setData(Qt.DisplayRole, int(comp_data.get('quantity', 0)));
            self.table_widget.setItem(row_position, 5, qty_item)
            min_qty_item = QTableWidgetItem();
            min_qty_item.setData(Qt.DisplayRole, int(comp_data.get('min_quantity', 0)));
            self.table_widget.setItem(row_position, 6, min_qty_item)
            needed_item = QTableWidgetItem();
            needed_item.setData(Qt.DisplayRole, to_order_val);
            self.table_widget.setItem(row_position, 7, needed_item)
        self.table_widget.resizeColumnsToContents();
        self.table_widget.setSortingEnabled(True)

    def get_order_data_for_export(self):
        data = [];
        headers = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
        for row in range(self.table_widget.rowCount()):
            row_data = {headers[i]: self.table_widget.item(row, i).text() if self.table_widget.item(row, i) else "" for
                        i in range(len(headers))}
            if int(row_data.get(headers[7], 0)) > 0: data.append(row_data)
        return data, headers

    def export_to_csv(self):
        order_data, headers = self.get_order_data_for_export()
        if not order_data: QMessageBox.information(self, "Ma'lumot yo'q",
                                                   "Buyurtma ro'yxatiga eksport qilish uchun komponentlar yo'q."); return
        options = QFileDialog.Options();
        last_export_dir = get_setting("last_export_dir", os.path.expanduser("~"))
        file_path, _ = QFileDialog.getSaveFileName(self, "Buyurtma ro'yxatini eksport qilish",
                                                   os.path.join(last_export_dir, "buyurtma_ombor_uchun.csv"),
                                                   "CSV-fayllar (*.csv)", options=options)
        if file_path:
            set_setting("last_export_dir", os.path.dirname(file_path))
            try:
                if not file_path.lower().endswith(".csv"): file_path += ".csv"
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    if order_data: writer = csv.DictWriter(csvfile, fieldnames=headers,
                                                           delimiter=';'); writer.writeheader(); writer.writerows(
                        order_data)
                QMessageBox.information(self, "Eksport Muvaffaqiyatli", f"Buyurtma ro'yxati '{file_path}' ga saqlandi.")
            except Exception as e:
                QMessageBox.critical(self, "Eksport xatosi", f"Ro'yxatni eksport qilib bo'lmadi: {e}")


def generate_order_list_action(main_window_instance):
    all_components = get_all_components()
    if not all_components: QMessageBox.information(main_window_instance, "Ma'lumot yo'q",
                                                   "Bazadagi komponentlar yo'q."); return
    low_stock_components = [comp for comp in all_components if
                            comp.get('min_quantity', 0) > 0 and comp.get('quantity', 0) < comp.get('min_quantity', 0)]
    if not low_stock_components: QMessageBox.information(main_window_instance, "Hammasi joyida",
                                                         "Buyurtma talab qiladigan komponentlar yo'q (minimal miqdordan kam)."); return
    dialog = GenerateOrderListDialog(main_window_instance, low_stock_components=low_stock_components);
    dialog.exec_()


def _export_revision_to_excel_with_highlighting(main_window, file_path, dataframe):
    try:
        def highlight_insufficient(row):
            if 'Sotib Olish Kerak' in row and row['Sotib Olish Kerak'] > 0:
                return ['background-color: #FFC7CE'] * len(row)
            else:
                return [''] * len(row)

        styled_df = dataframe.style.apply(highlight_insufficient, axis=1)
        styled_df.to_excel(file_path, index=False, engine='openpyxl')

        QMessageBox.information(main_window, "Reviziya Yakunlandi",
                                f"Reviziya natijalari '{file_path}' fayliga saqlandi.\n"
                                "Yetishmayotgan komponentlar qizil rang bilan belgilandi.")
    except Exception as e:
        QMessageBox.critical(main_window, "Excel Eksport Xatosi",
                             f"Stillashtirilgan Excel faylini saqlashda xatolik:\n{e}")


# --- ASOSIY FUNKSIYA: Proyekt Reviziyasi (YANGILANGAN) ---
def perform_project_revision_action(main_window):
    options = QFileDialog.Options()
    last_import_dir = get_setting("last_import_dir", os.path.expanduser("~"))
    file_filter = "Excel fayllari (*.xlsx *.xls);;CSV fayllar (*.csv);;Barcha fayllar (*)"
    bom_file_path, _ = QFileDialog.getOpenFileName(main_window, "Proyekt uchun komponentlar ro'yxatini (BOM) tanlang",
                                                   last_import_dir, file_filter, options=options)
    if not bom_file_path:
        return
    set_setting("last_import_dir", os.path.dirname(bom_file_path))

    try:
        bom_df = None
        if bom_file_path.lower().endswith('.csv'):
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252', 'cp1251']
            last_exception = None
            for enc in encodings_to_try:
                try:
                    bom_df = pd.read_csv(bom_file_path, encoding=enc, skip_blank_lines=True)
                    print(f"MA'LUMOT: CSV fayl '{enc}' kodirovkasi bilan o'qildi.")
                    break
                except Exception as e:
                    last_exception = e
                    print(f"OGOHLANTIRISH: CSV faylni '{enc}' bilan o'qishda xato: {e}")
            if bom_df is None and last_exception is not None:
                raise last_exception
        elif bom_file_path.lower().endswith(('.xlsx', '.xls')):
            bom_df = pd.read_excel(bom_file_path)
        else:
            QMessageBox.warning(main_window, "Fayl formati xatosi", "Qo'llab-quvvatlanmaydigan fayl formati.")
            return

        if bom_df is None:
            QMessageBox.warning(main_window, "Fayl Xatosi", "BOM fayli bo'sh yoki o'qib bo'lmadi.")
            return

    except Exception as e:
        QMessageBox.critical(main_window, "Faylni o'qish xatosi", f"BOM faylini o'qishda xatolik:\n{e}")
        return

    # --- O'ZGARTIRILGAN QISM: Endi "Nomi" ustuni ham qidiriladi ---
    name_col = None
    part_number_col = None
    quantity_col = None

    possible_name_cols = ['Nomi', 'Name', 'Nomi', 'Component Name', 'Description']
    possible_pn_cols = ['Qism Raqami', 'Part Number', 'PN', 'Part_Number', 'part_number', 'Designator', 'Reference']
    possible_qty_cols = ['Kerakli Miqdor', 'Required Quantity', 'Qty', 'Miqdori', 'Quantity', 'required_quantity',
                         'Count']

    bom_df_columns_lower = {col.lower().strip(): col for col in bom_df.columns}

    for p_name in possible_name_cols:
        if p_name.lower() in bom_df_columns_lower: name_col = bom_df_columns_lower[p_name.lower()]; break
    for ppn in possible_pn_cols:
        if ppn.lower() in bom_df_columns_lower: part_number_col = bom_df_columns_lower[ppn.lower()]; break
    for pqc in possible_qty_cols:
        if pqc.lower() in bom_df_columns_lower: quantity_col = bom_df_columns_lower[pqc.lower()]; break

    # Endi "Qism Raqami" yoki "Nomi" dan biri va "Kerakli Miqdor" bo'lishi shart
    if (not part_number_col and not name_col) or not quantity_col:
        QMessageBox.warning(main_window, "BOM Fayl Xatosi",
                            f"BOM faylida kerakli ustunlar topilmadi.\n\n"
                            f"Kerakli ustunlar: 'Kerakli Miqdor' (yoki 'Quantity') va 'Qism Raqami' (yoki 'Part Number') YOKI 'Nomi' (yoki 'Name').\n\n"
                            f"Topilgan ustunlar: {', '.join(bom_df.columns)}");
        return

    progress_dialog = QProgressDialog("Reviziya amalga oshirilmoqda...", "Bekor qilish", 0, len(bom_df), main_window)
    progress_dialog.setWindowModality(Qt.WindowModal);
    progress_dialog.setMinimumDuration(0);
    progress_dialog.setValue(0);
    QApplication.processEvents()

    revision_results = []
    all_db_components_list = get_all_components()

    # Endi ikkita lug'at yaratamiz: biri PN bo'yicha, ikkinchisi Nomi bo'yicha
    all_db_components_dict_pn = {str(comp.get('part_number', '')).lower().strip(): comp for comp in
                                 all_db_components_list if comp.get('part_number')}
    all_db_components_dict_name = {str(comp.get('name', '')).lower().strip(): comp for comp in all_db_components_list if
                                   comp.get('name')}

    for index, row in bom_df.iterrows():
        if progress_dialog.wasCanceled(): main_window.statusBar().showMessage("Reviziya bekor qilindi.", 3000); return

        # BOM dan 'Nomi', 'Qism Raqami' va 'Kerakli Miqdor' ni olish
        name_bom_raw = row.get(name_col) if name_col else None
        part_number_bom_raw = row.get(part_number_col) if part_number_col else None
        required_qty_bom_raw = row.get(quantity_col)

        name_bom = str(name_bom_raw).strip() if pd.notna(name_bom_raw) else ""
        part_number_bom = str(part_number_bom_raw).strip() if pd.notna(part_number_bom_raw) else ""

        required_qty_bom = 0
        if pd.notna(required_qty_bom_raw):
            try:
                required_qty_bom = int(float(str(required_qty_bom_raw).replace(',', '.')))
            except (ValueError, TypeError):
                print(
                    f"OGOHLANTIRISH: Miqdorni o'qishda xato: '{required_qty_bom_raw}' (qator {index + 2})"); required_qty_bom = 0

        # Agar na PN, na Nomi bo'lsa yoki miqdor 0 bo'lsa, qatorni o'tkazib yuborish
        if (not part_number_bom and not name_bom) or required_qty_bom <= 0:
            progress_dialog.setValue(index + 1);
            QApplication.processEvents();
            continue

        db_comp = None
        # 1. Avval PN bo'yicha qidirish (agar mavjud bo'lsa)
        if part_number_bom:
            db_comp = all_db_components_dict_pn.get(part_number_bom.lower())

        # 2. Agar PN bo'yicha topilmasa, Nomi bo'yicha qidirish (agar mavjud bo'lsa)
        if db_comp is None and name_bom:
            db_comp = all_db_components_dict_name.get(name_bom.lower())

        stock_qty = 0
        comp_name = name_bom if name_bom else part_number_bom  # Agar bazada topilmasa, BOMdagi nomni ishlatish
        comp_category = "-";
        comp_value = "-";
        comp_package = "-"

        if db_comp:  # Agar komponent bazada topilsa
            stock_qty = int(db_comp.get('quantity', 0))
            comp_name = db_comp.get('name', comp_name)  # Bazadagi nomni afzal ko'rish
            comp_category = db_comp.get('category_name', "-")
            comp_value = db_comp.get('value', "-")
            comp_package = db_comp.get('package_type_name', "-")

        to_buy_qty = max(0, required_qty_bom - stock_qty)
        revision_results.append({
            "Nomi": comp_name,
            "Qism Raqami": part_number_bom,
            "Kategoriya": comp_category,
            "Qiymati": comp_value,
            "Korpus": comp_package,
            "Kerakli Miqdor (Proyekt)": required_qty_bom,
            "Omborda Mavjud": stock_qty,
            "Sotib Olish Kerak": to_buy_qty,
            "Holati": "Yetarli" if to_buy_qty == 0 else (
                "Qisman Yetarli" if stock_qty > 0 else "MBda Yo'q" if db_comp is None else "Yo'q")
        })
        progress_dialog.setValue(index + 1);
        QApplication.processEvents()
    progress_dialog.close()
    # --- O'ZGARTIRISH TUGADI ---

    if not revision_results:
        QMessageBox.information(main_window, "Reviziya Yakunlandi",
                                "BOM faylida qayta ishlanadigan ma'lumotlar topilmadi.")
        return

    options = QFileDialog.Options()
    last_export_dir = get_setting("last_export_dir", os.path.expanduser("~"))
    save_filter = "Excel fayllar (*.xlsx);;CSV fayllar (*.csv)"
    output_file_path, selected_filter = QFileDialog.getSaveFileName(main_window, "Reviziya natijalarini saqlash",
                                                                    os.path.join(last_export_dir,
                                                                                 "proyekt_reviziya_natijasi"),
                                                                    save_filter, options=options)

    if output_file_path:
        set_setting("last_export_dir", os.path.dirname(output_file_path))
        results_df = pd.DataFrame(revision_results)

        if selected_filter.startswith("Excel"):
            if not output_file_path.lower().endswith((".xlsx", ".xls")):
                output_file_path += ".xlsx"
            _export_revision_to_excel_with_highlighting(main_window, output_file_path, results_df)
        else:
            if not output_file_path.lower().endswith(".csv"):
                output_file_path += ".csv"
            try:
                results_df.to_csv(output_file_path, index=False, sep=';', encoding='utf-8-sig')
                QMessageBox.information(main_window, "Reviziya Yakunlandi",
                                        f"Reviziya natijalari '{output_file_path}' fayliga saqlandi.\n"
                                        "(CSV formatida rangli belgilash mumkin emas).")
            except Exception as e:
                QMessageBox.critical(main_window, "Saqlash Xatosi", f"CSV faylga saqlashda xatolik: {e}")

    main_window.statusBar().showMessage("Proyekt reviziyasi yakunlandi.", 5000)