from postgres_utils import PostgresUtils
from database_config import DatabaseConfig
import json

def main():
    print("🚀 Генератор синтетических данных для PostgreSQL")
    print("=" * 50)

    # Загрузка конфигурации из JSON
    config = DatabaseConfig.from_json('config.json')
    if not config:
        print("❌ Не удалось загрузить конфигурацию")
        return

    pg_utils = PostgresUtils(config)
    
    # Проверка соединения 
    if not pg_utils.test_connection():
        print("❌ Нет соединения с базой данных!")
        return

    print(f"✅ Успешное подключение к базе данных '{config.database}'")

    # Получение списка таблиц
    tables = pg_utils.get_all_tables()
    if not tables:
        print(f"❌ В схеме '{config.schema}' не найдено таблиц")
        return

    # Загрузка конфигурации генерации
    generation_config = pg_utils.generation_config
    if not generation_config:
        print("❌ Ошибка загрузки конфигурации генерации")
        return

    # Обработка таблиц из конфигурации
    if 'tables' not in generation_config:
        print("❌ В конфигурации не найдены таблицы для обработки")
        return

    # Собираем существующие значения внешних ключей для всех таблиц
    existing_fk_values = {}
    
    # Сначала обрабатываем родительские таблицы (без внешних ключей)
    parent_tables = []
    child_tables = []
    
    for table_config in generation_config['tables']:
        table_name = table_config.get('table_name')
        if table_name not in tables:
            print(f"❌ Таблица '{table_name}' не найдена в схеме '{config.schema}'")
            continue
            
        # Проверяем, есть ли у таблицы внешние ключи
        foreign_keys = pg_utils.get_foreign_keys(table_name)
        if foreign_keys:
            child_tables.append(table_config)
        else:
            parent_tables.append(table_config)

    # Обрабатываем сначала родительские таблицы
    for table_config in parent_tables:
        table_name = table_config.get('table_name')
        rows_to_generate = table_config.get('rows_to_generate', 100)
        
        print(f"\n🔍 Обработка родительской таблицы: {table_name}")
        print(f"📊 Будет сгенерировано строк: {rows_to_generate}")
        
        # Получение структуры таблицы
        structure = pg_utils.get_table_structure(table_name)
        if not structure:
            print(f"❌ Не удалось получить структуру таблицы '{table_name}'")
            continue

        # Показ структуры таблицы
        pg_utils.display_table_structure(table_name, structure)

        # Генерация и вставка данных
        print(f"\n Генерация {rows_to_generate} строк для таблицы '{table_name}'...")
        success = pg_utils.insert_data_with_fk_handling(table_name, rows_to_generate)
        
        if success:
            # Сохраняем сгенерированные значения для использования в дочерних таблицах
            pg_utils._collect_generated_fk_values(table_name, existing_fk_values)
        else:
            print(f"❌ Ошибка при обработке таблицы '{table_name}'")

    # Затем обрабатываем дочерние таблицы
    for table_config in child_tables:
        table_name = table_config.get('table_name')
        rows_to_generate = table_config.get('rows_to_generate', 100)
        
        print(f"\n🔍 Обработка дочерней таблицы: {table_name}")
        print(f"📊 Будет сгенерировано строк: {rows_to_generate}")
        
        # Получение структуры таблицы
        structure = pg_utils.get_table_structure(table_name)
        if not structure:
            print(f"❌ Не удалось получить структуру таблицы '{table_name}'")
            continue

        # Показ структуры таблицы
        pg_utils.display_table_structure(table_name, structure)

        # Генерация и вставка данных с использованием существующих FK значений
        print(f"\n Генерация {rows_to_generate} строк для таблицы '{table_name}'...")
        success = pg_utils.insert_data_with_fk_handling(table_name, rows_to_generate)
        
        if not success:
            print(f"❌ Ошибка при обработке таблицы '{table_name}'")

    print("\n👋 Завершение работы")

if __name__ == "__main__":
    main()