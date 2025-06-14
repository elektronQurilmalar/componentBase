# ElektronKomponentlarUchoti/app_logic/db_manager.py
import sqlite3
import os
import re  # Satrlarni tozalash uchun

try:
    from utils.component_packages import COMPONENT_PACKAGES as INITIAL_COMPONENT_PACKAGES_DEFINITIONS
    from utils.config_manager import get_setting  # Maxsus maydonlarni olish uchun
except ImportError:
    print("OGOHLANTIRISH: Kerakli modullar topilmadi (db_manager.py).")
    INITIAL_COMPONENT_PACKAGES_DEFINITIONS = {}
    get_setting = lambda key, default: default

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_NAME = "components_inventory.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

os.makedirs(DB_DIR, exist_ok=True)

_STANDARD_COMPONENT_FIELDS_INFO_LIST = [
    {'db_key': 'id', 'display_name_uz': 'ID', 'type': 'integer_pk', 'default_visible': True, 'editable': False,
     'required': True, 'is_custom': False},
    {'db_key': 'name', 'display_name_uz': 'Nomi', 'type': 'text', 'default_visible': True, 'editable': True,
     'required': True, 'is_custom': False},
    {'db_key': 'category_id', 'display_name_uz': 'Kategoriya', 'type': 'fk_category', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False, 'related_name_key': 'category_name'},
    {'db_key': 'part_number', 'display_name_uz': 'Qism Raqami', 'type': 'text', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'manufacturer', 'display_name_uz': 'Ishlab chiqaruvchi', 'type': 'text', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'value', 'display_name_uz': 'Qiymati', 'type': 'text', 'default_visible': True, 'editable': True,
     'required': False, 'is_custom': False},
    {'db_key': 'package_type_id', 'display_name_uz': 'Korpus', 'type': 'fk_package', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False, 'related_name_key': 'package_type_name'},
    {'db_key': 'quantity', 'display_name_uz': 'Miqdori', 'type': 'integer', 'default_visible': True, 'editable': True,
     'required': False, 'is_custom': False},
    {'db_key': 'min_quantity', 'display_name_uz': 'Min.Miqdor', 'type': 'integer', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'location_id', 'display_name_uz': 'Joylashuvi', 'type': 'fk_location', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False, 'related_name_key': 'location_name'},
    {'db_key': 'project', 'display_name_uz': 'Loyiha', 'type': 'text', 'default_visible': True, 'editable': True,
     'required': False, 'is_custom': False},
    {'db_key': 'description', 'display_name_uz': 'Tavsif', 'type': 'text_area', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'datasheet_path', 'display_name_uz': 'Datasheet', 'type': 'file_path', 'default_visible': True,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'reminder_date', 'display_name_uz': 'Eslatma sanasi', 'type': 'date', 'default_visible': False,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'reminder_text', 'display_name_uz': 'Eslatma', 'type': 'text', 'default_visible': False,
     'editable': True, 'required': False, 'is_custom': False},
    {'db_key': 'created_at', 'display_name_uz': 'Yaratilgan sana', 'type': 'timestamp', 'default_visible': False,
     'editable': False, 'required': False, 'is_custom': False},
    {'db_key': 'updated_at', 'display_name_uz': 'Yangilangan sana', 'type': 'timestamp', 'default_visible': False,
     'editable': False, 'required': False, 'is_custom': False},
]


def get_all_possible_component_fields_info(include_fk_names=False):
    all_fields = [f.copy() for f in _STANDARD_COMPONENT_FIELDS_INFO_LIST]
    custom_text_fields_config = get_setting("custom_text_fields", [])
    for custom_field_conf in custom_text_fields_config:
        if not any(sf['db_key'] == custom_field_conf['db_key'] for sf in all_fields):
            all_fields.append({
                'db_key': custom_field_conf['db_key'],
                'display_name_uz': custom_field_conf['display_name_uz'],
                'type': 'text',
                'default_visible': True,
                'editable': True,
                'required': False,
                'is_custom': True  # Maxsus maydon ekanligini belgilash
            })
    return all_fields


def sanitize_column_name(name):
    name = name.lower()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^a-z0-9_]', '', name)
    if not name or name.isdigit() or name.startswith('_'):
        name = "custom_" + name
    return name


def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"MB ulanish xatosi: {e}")
        return None


def close_db_connection(conn):
    if conn: conn.close()


def create_tables():
    conn = get_db_connection()
    if conn is None: return False
    tables_created_or_exist = False
    try:
        cursor = conn.cursor()
        standard_fields_for_table_creation = []
        for field_info in _STANDARD_COMPONENT_FIELDS_INFO_LIST:
            if field_info['db_key'] == 'id':
                standard_fields_for_table_creation.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
            elif field_info['type'] == 'fk_category':
                standard_fields_for_table_creation.append("category_id INTEGER")
            elif field_info['type'] == 'fk_package':
                standard_fields_for_table_creation.append("package_type_id INTEGER")
            elif field_info['type'] == 'fk_location':
                standard_fields_for_table_creation.append("location_id INTEGER")
            elif field_info['type'] == 'integer':
                default_val = "DEFAULT 0" if field_info['db_key'] in ['quantity', 'min_quantity'] else ""
                standard_fields_for_table_creation.append(f"{field_info['db_key']} INTEGER {default_val}")
            elif field_info['type'] == 'timestamp':
                standard_fields_for_table_creation.append(f"{field_info['db_key']} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            else:
                not_null = "NOT NULL" if field_info['db_key'] == 'name' else ""
                standard_fields_for_table_creation.append(f"{field_info['db_key']} TEXT {not_null}")
        standard_fields_for_table_creation.append(
            "FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL")
        standard_fields_for_table_creation.append(
            "FOREIGN KEY (package_type_id) REFERENCES package_types (id) ON DELETE SET NULL")
        standard_fields_for_table_creation.append(
            "FOREIGN KEY (location_id) REFERENCES storage_locations (id) ON DELETE SET NULL")
        components_table_sql = f"""
            CREATE TABLE IF NOT EXISTS components (
                {', '.join(standard_fields_for_table_creation)}
            )
        """
        cursor.execute(components_table_sql)
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS package_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS storage_locations (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_components_updated_at
            AFTER UPDATE ON components
            FOR EACH ROW
            BEGIN
                UPDATE components SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)
        conn.commit()
        print("Jadvallar yaratildi yoki allaqachon mavjud.")
        tables_created_or_exist = True
        custom_text_fields_config = get_setting("custom_text_fields", [])
        for custom_field_conf in custom_text_fields_config:
            _ensure_column_exists(conn, 'components', custom_field_conf['db_key'], 'TEXT')
        populate_initial_reference_data(conn)
    except sqlite3.Error as e:
        print(f"Jadval yaratish xatosi: {e}")
    finally:
        close_db_connection(conn)
    return tables_created_or_exist


def _ensure_column_exists(conn, table_name, column_name, column_type):
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            conn.commit()
            print(f"MA'LUMOT: '{table_name}' jadvaliga '{column_name}' ({column_type}) ustuni qo'shildi.")
    except sqlite3.Error as e:
        print(f"XATOLIK: '{table_name}' jadvaliga '{column_name}' ustunini qo'shishda: {e}")


def populate_initial_reference_data(conn):
    if conn is None: return
    try:
        cursor = conn.cursor()
        # --- O'ZGARTIRILGAN QISM START ---
        # Barcha kategoriyalarni component_packages.py dan olish
        initial_categories = list(INITIAL_COMPONENT_PACKAGES_DEFINITIONS.keys())

        # Barcha unikal korpus turlarini yig'ish
        all_packages_from_definitions = set()
        for cat_name, pkg_list in INITIAL_COMPONENT_PACKAGES_DEFINITIONS.items():
            for pkg_name in pkg_list:
                all_packages_from_definitions.add(pkg_name)

        # "Boshqa" ni qo'shish (agar yo'q bo'lsa), chunki u umumiy variant
        if "Boshqa" not in all_packages_from_definitions:
            all_packages_from_definitions.add("Boshqa")

        # Kategoriyalarni bazaga kiritish
        inserted_categories_count = 0
        for category_name in initial_categories:
            try:
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category_name,))
                if cursor.rowcount > 0: inserted_categories_count += 1
            except sqlite3.Error as e_inner:
                print(f"'{category_name}' kategoriyasini kiritishda xato: {e_inner}")

        # Korpus turlarini bazaga kiritish
        inserted_packages_count = 0
        for package_name in sorted(list(all_packages_from_definitions)):
            try:
                cursor.execute("INSERT OR IGNORE INTO package_types (name) VALUES (?)", (package_name,))
                if cursor.rowcount > 0: inserted_packages_count += 1
            except sqlite3.Error as e_inner:
                print(f"'{package_name}' paket turini kiritishda xato: {e_inner}")

        # --- O'ZGARTIRILGAN QISM END ---

        # Boshlang'ich saqlash joylari (o'zgarishsiz)
        initial_locations = ["Quti A1", "Polka B2", "Stol usti"]
        inserted_locations_count = 0
        for loc_name in initial_locations:
            try:
                cursor.execute("INSERT OR IGNORE INTO storage_locations (name) VALUES (?)", (loc_name,))
                if cursor.rowcount > 0: inserted_locations_count += 1
            except sqlite3.Error as e_inner:
                print(f"'{loc_name}' saqlash joyini kiritishda xato: {e_inner}")
        if inserted_categories_count > 0 or inserted_packages_count > 0 or inserted_locations_count > 0:
            print(
                f"Boshlang'ich ma'lumotlar kiritildi: {inserted_categories_count} ta kategoriya, {inserted_packages_count} ta paket turi, {inserted_locations_count} ta joy.")
            conn.commit()
    except Exception as e:
        print(f"Boshlang'ich ma'lumotlarni kiritishda xato: {e}")


def get_or_create_id(table_name, name, conn):
    if not name or not name.strip() or not table_name or conn is None: return None
    row_id = None;
    last_id = -1
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {table_name} WHERE LOWER(name) = LOWER(?)", (name.strip(),))
        row = cursor.fetchone()
        if row:
            row_id = row['id']
        else:
            cursor.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (name.strip(),))
            last_id = cursor.lastrowid;
            row_id = last_id
    except sqlite3.IntegrityError:
        try:
            cursor.execute(f"SELECT id FROM {table_name} WHERE LOWER(name) = LOWER(?)", (name.strip(),))
            row = cursor.fetchone();
            if row: row_id = row['id']
        except sqlite3.Error as e_inner:
            print(f"'{name.strip()}' uchun IDni qayta olishda xato: {e_inner}")
    except sqlite3.Error as e:
        print(f"'{name.strip()}' ({table_name}) uchun get_or_create_id da xato: {e}")
    return row_id if row_id is not None else (last_id if last_id > 0 else None)


get_or_create_category_id = lambda name, conn: get_or_create_id("categories", name, conn)
get_or_create_package_type_id = lambda name, conn: get_or_create_id("package_types", name, conn)
get_or_create_location_id = lambda name, conn: get_or_create_id("storage_locations", name, conn)


def add_component(data):
    conn = get_db_connection()
    if conn is None: return None
    new_id = None
    try:
        all_editable_fields_info = [f for f in get_all_possible_component_fields_info() if f.get('editable')]
        field_names_for_sql = []
        field_values_for_sql = []
        for field_info in all_editable_fields_info:
            db_key = field_info['db_key']
            data_key = db_key
            if field_info['type'] == 'fk_category':
                field_names_for_sql.append('category_id')
                field_values_for_sql.append(get_or_create_category_id(data.get('category'), conn))
            elif field_info['type'] == 'fk_package':
                field_names_for_sql.append('package_type_id')
                field_values_for_sql.append(
                    get_or_create_package_type_id(data.get('package_type'), conn))
            elif field_info['type'] == 'fk_location':
                field_names_for_sql.append('location_id')
                field_values_for_sql.append(get_or_create_location_id(data.get('location'), conn))
            elif db_key not in ['id', 'created_at', 'updated_at']:
                field_names_for_sql.append(db_key)
                default_value = 0 if field_info['type'] == 'integer' and data.get(data_key) is None else None
                field_values_for_sql.append(data.get(data_key, default_value))
        if not field_names_for_sql:
            print("XATOLIK: Komponent qo'shish uchun tahrirlanadigan maydonlar topilmadi.")
            return None
        placeholders = ", ".join(["?"] * len(field_names_for_sql))
        sql = f"INSERT INTO components ({', '.join(field_names_for_sql)}) VALUES ({placeholders})"
        cursor = conn.cursor()
        cursor.execute(sql, tuple(field_values_for_sql))
        new_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        print(f"Komponent qo'shishda xato ({type(e).__name__}): {e}. Ma'lumot: {data}")
    finally:
        close_db_connection(conn)
    return new_id


def get_all_components(filters=None):
    conn = get_db_connection();
    if conn is None: return []
    try:
        all_fields_info = get_all_possible_component_fields_info()
        select_parts = []
        for field_info in all_fields_info:
            db_key = field_info['db_key']
            output_key = field_info.get('related_name_key', db_key)
            if field_info['type'] == 'fk_category':
                select_parts.append(f"cat.name as {output_key}")
            elif field_info['type'] == 'fk_package':
                select_parts.append(f"pkg.name as {output_key}")
            elif field_info['type'] == 'fk_location':
                select_parts.append(f"loc.name as {output_key}")
            elif db_key == 'id':
                select_parts.append(f"comp.id as id")
            else:
                select_parts.append(f"comp.{db_key} as {output_key}")
        unique_select_parts = list(dict.fromkeys(select_parts))
        select_fields_str = ", ".join(unique_select_parts)
        base_sql = f"""
            SELECT {select_fields_str}
            FROM components comp
            LEFT JOIN categories cat ON comp.category_id = cat.id
            LEFT JOIN package_types pkg ON comp.package_type_id = pkg.id
            LEFT JOIN storage_locations loc ON comp.location_id = loc.id
        """
        where_clauses = [];
        params = []
        if filters:
            search_text_val = filters.get('search_text')
            searchable_db_keys_from_info = [
                f"comp.{fi['db_key']}" for fi in all_fields_info
                if fi['type'] in ['text', 'text_area', 'file_path'] or fi['db_key'] == 'project'
            ]
            searchable_db_keys_from_info.extend(["cat.name", "pkg.name", "loc.name"])
            if search_text_val and not (filters.get('adv_name') or filters.get('adv_part_number') or filters.get(
                    'adv_manufacturer') or filters.get('adv_value')):
                st = f"%{search_text_val}%"
                search_field_clauses = [f"LOWER({key}) LIKE LOWER(?)" for key in searchable_db_keys_from_info]
                where_clauses.append(f"({' OR '.join(search_field_clauses)})")
                params.extend([st] * len(searchable_db_keys_from_info))
            if filters.get('category_name') and filters['category_name'] != "Barcha kategoriyalar":
                where_clauses.append("cat.name = ?");
                params.append(filters['category_name'])
            if filters.get('project_name') and filters['project_name'] != "Barcha loyihalar":
                if filters['project_name'] == '':
                    where_clauses.append("(comp.project IS NULL OR comp.project = '')")
                else:
                    where_clauses.append("comp.project = ?");
                    params.append(filters['project_name'])
            if filters.get('low_stock_only'):
                where_clauses.append("(comp.min_quantity > 0 AND comp.quantity <= comp.min_quantity)")
            if filters.get('adv_name'): where_clauses.append("LOWER(comp.name) LIKE LOWER(?)"); params.append(
                f"%{filters['adv_name']}%")
            if filters.get('adv_part_number'): where_clauses.append(
                "LOWER(comp.part_number) LIKE LOWER(?)"); params.append(f"%{filters['adv_part_number']}%")
            if filters.get('adv_manufacturer'): where_clauses.append(
                "LOWER(comp.manufacturer) LIKE LOWER(?)"); params.append(f"%{filters['adv_manufacturer']}%")
            if filters.get('adv_value'): where_clauses.append("LOWER(comp.value) LIKE LOWER(?)"); params.append(
                f"%{filters['adv_value']}%")
            if 'quantity_min' in filters and filters['quantity_min'] != -1:
                where_clauses.append("comp.quantity >= ?");
                params.append(filters['quantity_min'])
            if 'quantity_max' in filters and filters['quantity_max'] != -1:
                where_clauses.append("comp.quantity <= ?");
                params.append(filters['quantity_max'])
        if where_clauses: base_sql += " WHERE " + " AND ".join(where_clauses)
        base_sql += " ORDER BY comp.id DESC"
        cursor = conn.cursor();
        cursor.execute(base_sql, tuple(params))
        components = cursor.fetchall()
        return [dict(row) for row in components]
    except sqlite3.Error as e:
        print(f"Komponentlarni olishda xato: {e}");
        return []
    finally:
        close_db_connection(conn)


def get_component_by_id(component_id):
    conn = get_db_connection();
    if conn is None: return None
    try:
        all_fields_info = get_all_possible_component_fields_info()
        select_parts = []
        for field_info in all_fields_info:
            db_key = field_info['db_key']
            output_key = field_info.get('related_name_key', db_key)
            if field_info['type'] == 'fk_category':
                select_parts.append(f"cat.name as {output_key}")
            elif field_info['type'] == 'fk_package':
                select_parts.append(f"pkg.name as {output_key}")
            elif field_info['type'] == 'fk_location':
                select_parts.append(f"loc.name as {output_key}")
            elif db_key == 'id':
                select_parts.append(f"comp.id as id")
            else:
                select_parts.append(f"comp.{db_key} as {output_key}")
        unique_select_parts = list(dict.fromkeys(select_parts))
        select_fields_str = ", ".join(unique_select_parts)
        sql = f"""
            SELECT {select_fields_str}
            FROM components comp
            LEFT JOIN categories cat ON comp.category_id = cat.id
            LEFT JOIN package_types pkg ON comp.package_type_id = pkg.id
            LEFT JOIN storage_locations loc ON comp.location_id = loc.id
            WHERE comp.id = ?
        """
        cursor = conn.cursor();
        cursor.execute(sql, (component_id,))
        component = cursor.fetchone()
        return dict(component) if component else None
    except sqlite3.Error as e:
        print(f"ID={component_id} komponentni olishda xato: {e}");
        return None
    finally:
        close_db_connection(conn)


def update_component(component_id, data):
    conn = get_db_connection()
    if conn is None: return False
    success = False
    try:
        all_editable_fields_info = [f for f in get_all_possible_component_fields_info() if f.get('editable')]
        set_clauses = []
        field_values_for_sql = []
        for field_info in all_editable_fields_info:
            db_key = field_info['db_key']
            data_key = db_key
            if field_info['type'] == 'fk_category':
                set_clauses.append('category_id = ?')
                field_values_for_sql.append(get_or_create_category_id(data.get('category'), conn))
            elif field_info['type'] == 'fk_package':
                set_clauses.append('package_type_id = ?')
                field_values_for_sql.append(get_or_create_package_type_id(data.get('package_type'), conn))
            elif field_info['type'] == 'fk_location':
                set_clauses.append('location_id = ?')
                field_values_for_sql.append(get_or_create_location_id(data.get('location'), conn))
            elif db_key not in ['id', 'created_at', 'updated_at']:
                set_clauses.append(f"{db_key} = ?")
                default_value = 0 if field_info['type'] == 'integer' and data.get(data_key) is None else None
                field_values_for_sql.append(data.get(data_key, default_value))
        if not set_clauses:
            print("XATOLIK: Komponentni yangilash uchun tahrirlanadigan maydonlar topilmadi.")
            return False
        field_values_for_sql.append(component_id)
        sql = f"UPDATE components SET {', '.join(set_clauses)} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(sql, tuple(field_values_for_sql))
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Komponent yangilashda xato ({type(e).__name__}): {e}. Ma'lumot: {data}")
    finally:
        close_db_connection(conn)
    return success


def delete_component(component_id):
    conn = get_db_connection();
    if conn is None: return False
    success = False
    try:
        sql = "DELETE FROM components WHERE id = ?";
        cursor = conn.cursor()
        cursor.execute(sql, (component_id,));
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Komponent o'chirish xatosi: {e}")
    finally:
        close_db_connection(conn)
    return success


def get_distinct_project_names():
    conn = get_db_connection();
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT project FROM components WHERE project IS NOT NULL AND project != '' ORDER BY project ASC")
        projects = [row['project'] for row in cursor.fetchall()]
        return projects
    except sqlite3.Error as e:
        print(f"Unikal loyiha nomlarini olishda xato: {e}");
        return []
    finally:
        close_db_connection(conn)


def get_all_categories_names():
    conn = get_db_connection();
    if conn is None: return []
    try:
        cursor = conn.cursor();
        cursor.execute("SELECT name FROM categories ORDER BY name ASC")
        return [row['name'] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Kategoriya nomlarini olishda xato: {e}");
        return []
    finally:
        close_db_connection(conn)


def get_all_package_types_names():
    conn = get_db_connection();
    if conn is None: return []
    try:
        cursor = conn.cursor();
        cursor.execute("SELECT name FROM package_types ORDER BY name ASC")
        package_names = [row['name'] for row in cursor.fetchall()]
        # Bu yerda "Boshqa"ni qo'shish logikasi o'zgartirildi,
        # chunki u component_packages.py orqali qo'shiladi.
        if package_names and "Boshqa" not in package_names:
            has_specific_boshqa = any(name.startswith("Boshqa (") and name.endswith(")") for name in package_names)
            if not has_specific_boshqa:
                package_names.append("Boshqa")
                package_names.sort()
        elif not package_names:
            package_names.append("Boshqa")
        return package_names
    except sqlite3.Error as e:
        print(f"Paket turi nomlarini olishda xato: {e}");
        return []
    finally:
        close_db_connection(conn)


def get_all_storage_locations_names():
    conn = get_db_connection();
    if conn is None: return []
    try:
        cursor = conn.cursor();
        cursor.execute("SELECT name FROM storage_locations ORDER BY name ASC")
        return [row['name'] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Saqlash joyi nomlarini olishda xato: {e}");
        return []
    finally:
        close_db_connection(conn)


def add_category_db(name):
    conn = get_db_connection()
    if conn is None or not name or not name.strip(): return False
    try:
        get_or_create_category_id(name, conn);
        return True
    except sqlite3.Error as e:
        print(f"'{name}' uchun kategoriya qo'shishda MB xatosi: {e}");
        return False
    finally:
        close_db_connection(conn)


def delete_category_db(name):
    conn = get_db_connection();
    if conn is None: return False
    success = False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM components c JOIN categories cat ON c.category_id = cat.id WHERE LOWER(cat.name) = LOWER(?)",
            (name,))
        if cursor.fetchone()['count'] > 0: print(
            f"'{name}' kategoriyasini o'chirib bo'lmaydi, u ishlatilmoqda."); return False
        cursor.execute("DELETE FROM categories WHERE LOWER(name) = LOWER(?)", (name,));
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"'{name}' uchun kategoriya o'chirishda MB xatosi: {e}")
    finally:
        close_db_connection(conn)
    return success


def add_storage_location_db(name):
    conn = get_db_connection()
    if conn is None or not name or not name.strip(): return False
    try:
        get_or_create_location_id(name, conn);
        return True
    except sqlite3.Error as e:
        print(f"'{name}' uchun joy qo'shishda MB xatosi: {e}");
        return False
    finally:
        close_db_connection(conn)


def delete_storage_location_db(name):
    conn = get_db_connection();
    if conn is None: return False
    success = False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM components c JOIN storage_locations sl ON c.location_id = sl.id WHERE LOWER(sl.name) = LOWER(?)",
            (name,))
        if cursor.fetchone()['count'] > 0: print(f"'{name}' joyini o'chirib bo'lmaydi, u ishlatilmoqda."); return False
        cursor.execute("DELETE FROM storage_locations WHERE LOWER(name) = LOWER(?)", (name,));
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"'{name}' uchun joy o'chirishda MB xatosi: {e}")
    finally:
        close_db_connection(conn)
    return success


def drop_custom_column_from_components_table(column_to_drop_db_key):
    """
    'components' jadvalidan berilgan maxsus ustunni o'chiradi.
    SQLite < 3.35.0 uchun xatolik qaytaradi yoki ogohlantiradi.
    """
    conn = get_db_connection()
    if conn is None:
        print(f"XATOLIK: '{column_to_drop_db_key}' ustunini o'chirish uchun MB ga ulanib bo'lmadi.")
        return False

    safe_column_name = sanitize_column_name(column_to_drop_db_key)
    if not safe_column_name:
        print(f"XATOLIK: '{column_to_drop_db_key}' uchun yaroqsiz ustun nomi.")
        close_db_connection(conn)
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        version_str = cursor.fetchone()[0]
        version_tuple = tuple(map(int, version_str.split('.')))

        if version_tuple >= (3, 35, 0):
            print(
                f"MA'LUMOT: SQLite {version_str}. '{safe_column_name}' uchun 'ALTER TABLE DROP COLUMN' ishlatilmoqda.")
            cursor.execute("PRAGMA table_info(components);")
            columns = [row['name'] for row in cursor.fetchall()]
            if safe_column_name not in columns:
                print(
                    f"OGOHLANTIRISH: '{safe_column_name}' ustuni 'components' jadvalida topilmadi. O'chirish amalga oshirilmadi.")
                close_db_connection(conn)
                return True

            cursor.execute(f"ALTER TABLE components DROP COLUMN {safe_column_name};")
            conn.commit()
            print(f"MA'LUMOT: '{safe_column_name}' ustuni 'components' jadvalidan muvaffaqiyatli o'chirildi.")
        else:
            print(
                f"XATOLIK: SQLite versiyasi ({version_str}) 'DROP COLUMN' ni to'g'ridan-to'g'ri qo'llab-quvvatlamaydi. "
                f"'{safe_column_name}' ustunini xavfsiz o'chirish uchun, iltimos, SQLite-ni 3.35.0 yoki undan yuqori versiyaga yangilang, "
                "yoki ma'lumotlar bazasini qo'lda boshqaring (masalan, DB Browser for SQLite orqali).")
            close_db_connection(conn)
            return False
        return True
    except sqlite3.Error as e:
        print(f"XATOLIK: '{safe_column_name}' ustunini 'components' jadvalidan o'chirishda: {e}")
        return False
    finally:
        close_db_connection(conn)


if __name__ == '__main__':
    if create_tables():
        print("MB va jadvallar test uchun tayyor.")
    else:
        print("Ma'lumotlar bazasi va jadvallarni ishga tushirib bo'lmadi.")