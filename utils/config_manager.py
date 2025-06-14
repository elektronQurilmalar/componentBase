# ElektronKomponentlarUchoti/utils/config_manager.py
import json
import os

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_FILE_DIR)

CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "settings.json"

CONFIG_DIR_PATH = os.path.join(BASE_DIR, CONFIG_DIR_NAME)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, CONFIG_FILE_NAME)


def ensure_config_dir_exists():
    if not os.path.exists(CONFIG_DIR_PATH):
        try:
            os.makedirs(CONFIG_DIR_PATH, exist_ok=True)
            print(f"MA'LUMOT: Konfiguratsiya papkasi yaratildi: {CONFIG_DIR_PATH}")
        except OSError as e:
            print(f"KRITIK XATOLIK: Konfiguratsiya papkasini ('{CONFIG_DIR_PATH}') yaratib bo'lmadi: {e}")
            return False
    return True


DEFAULT_SETTINGS = {
    "theme": "Tizim (Yorqin)",
    "confirm_delete": True,
    "default_datasheet_dir": "",
    "last_import_dir": os.path.expanduser("~"),
    "last_export_dir": os.path.expanduser("~"),
    "visible_columns": [],
    "column_headers_uz": {},
    "custom_text_fields": [],  # YANGI: Maxsus matnli maydonlar uchun ro'yxat
    # Har bir element: {'db_key': 'custom_text_N', 'display_name_uz': 'Foydalanuvchi Nomi'}
}


def load_settings():
    if not ensure_config_dir_exists():
        print("OGOHLANTIRISH: Konfiguratsiya papkasi mavjud emas. Standart sozlamalar ishlatiladi.")
        return DEFAULT_SETTINGS.copy()

    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for key, value in DEFAULT_SETTINGS.items():
                    settings.setdefault(key, value)
                return settings
        else:
            print(f"MA'LUMOT: Sozlamalar fayli topilmadi. '{CONFIG_FILE_PATH}' da standart sozlamalar yaratiladi.")
            if save_settings(DEFAULT_SETTINGS.copy()):
                return DEFAULT_SETTINGS.copy()
            else:
                print("XATOLIK: Standart sozlamalarni saqlab bo'lmadi. Vaqtinchalik sozlamalar ishlatiladi.")
                return DEFAULT_SETTINGS.copy()

    except (IOError, json.JSONDecodeError) as e:
        print(f"Sozlamalarni yuklashda xatolik ({CONFIG_FILE_PATH}): {e}. Standart sozlamalar ishlatiladi.")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings_dict):
    if not ensure_config_dir_exists():
        print(f"XATOLIK: Konfiguratsiya papkasi mavjud emas. Sozlamalarni '{CONFIG_FILE_PATH}' ga saqlab bo'lmadi.")
        return False

    try:
        temp_file_path = CONFIG_FILE_PATH + ".tmp"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4, ensure_ascii=False)

        if os.path.exists(CONFIG_FILE_PATH): os.remove(CONFIG_FILE_PATH)
        os.rename(temp_file_path, CONFIG_FILE_PATH)

        print(f"Sozlamalar muvaffaqiyatli saqlandi: {CONFIG_FILE_PATH}")
        global APP_SETTINGS
        APP_SETTINGS = settings_dict.copy()  # APP_SETTINGS ni yangilash
        return True
    except (IOError, OSError) as e:
        print(f"Sozlamalarni '{CONFIG_FILE_PATH}' ga saqlashda xatolik: {e}")
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        return False


APP_SETTINGS = load_settings()


def get_setting(key, default=None):
    default_value_from_master = DEFAULT_SETTINGS.get(key)
    return APP_SETTINGS.get(key, default if default is not None else default_value_from_master)


def set_setting(key, value):
    APP_SETTINGS[key] = value
    return save_settings(APP_SETTINGS)


if __name__ == '__main__':
    print("config_manager.py ni test qilish...")
    print(f"Loyiha Asosiy Papkasi: {BASE_DIR}")
    print(f"Konfiguratsiya Papkasi: {CONFIG_DIR_PATH}")
    print(f"Konfiguratsiya Fayli: {CONFIG_FILE_PATH}")
    print("\nStandart sozlamalar:", DEFAULT_SETTINGS)
    current_settings = load_settings()
    print("Yuklangan sozlamalar:", current_settings)

    # Test custom_text_fields
    print("\nMaxsus matnli maydonlarni test qilish...")
    original_custom_fields = get_setting("custom_text_fields", [])
    test_field = {'db_key': 'custom_test_1', 'display_name_uz': 'Test Maydoni 1'}

    new_custom_fields = original_custom_fields + [test_field]
    if set_setting("custom_text_fields", new_custom_fields):
        print("Maxsus maydonlar muvaffaqiyatli o'rnatildi.")
        reloaded_fields = get_setting("custom_text_fields")
        print("Qayta yuklangan maxsus maydonlar:", reloaded_fields)
        if any(f['db_key'] == test_field['db_key'] for f in reloaded_fields):
            print("TEKSHIRILDI: Maxsus maydon to'g'ri saqlandi va qayta yuklandi.")
        else:
            print("XATOLIK: Maxsus maydon saqlanmadi yoki qayta yuklanmadi.")
        # Testni tozalash
        set_setting("custom_text_fields", original_custom_fields)
    else:
        print("XATOLIK: Maxsus maydonlarni o'rnatishda xatolik.")

    print("\nTest tugadi. config/settings.json faylini tekshiring.")