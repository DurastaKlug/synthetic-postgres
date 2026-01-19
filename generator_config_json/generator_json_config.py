import os
import json
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ConfigSelector:
    def __init__(self):
        self.examples_dir = "generator_config_json\examples"
        
    def get_available_configs(self):
        """Получает список доступных конфигов"""
        if not os.path.exists(self.examples_dir):
            return []
        
        configs = []
        for file in os.listdir(self.examples_dir):
            if file.endswith('.json'):
                configs.append(file)
        
        return sorted(configs)
    
    def show_menu(self):
        """Показывает меню выбора"""
        configs = self.get_available_configs()
        
        if not configs:
            print("❌ В папке examples нет конфигов")
            return None
        
        print("\n" + "="*50)
        print(" Выберите конфиг для генерации:")
        print("="*50)
        
        for i, config in enumerate(configs, 1):
            print(f"{i}. {config}")
        
        print(f"{len(configs) + 1}. 🚪 Выход")
        print("="*50)
        
        return configs
    
    def generate_from_config(self, config_file):
        """Генерирует полный конфиг из выбранного"""
        try:
            from database_config import DatabaseConfig
            from postgres_utils import PostgresUtils
            
            config_path = os.path.join(self.examples_dir, config_file)
            
            print(f"\n Генерация из: {config_file}")
            
            # Загружаем конфиг
            with open(config_path, 'r', encoding='utf-8') as f:
                minimal_config = json.load(f)
            
            # Создаем конфиг БД
            db_config = DatabaseConfig(**minimal_config['database'])
            pg_utils = PostgresUtils(db_config)
            
            if not pg_utils.test_connection():
                print("❌ Нет соединения с БД")
                return
            
            # Получаем таблицы
            all_tables = pg_utils.get_all_tables()
            if not all_tables:
                print("❌ В схеме нет таблиц")
                return
            
            # Определяем какие таблицы обрабатывать
            if 'tables' in minimal_config and minimal_config['tables']:
                tables_to_process = [t for t in minimal_config['tables'] if t in all_tables]
                print(f" Обработка указанных таблиц: {len(tables_to_process)}")
            else:
                tables_to_process = all_tables
                print(f" Обработка всех таблиц схемы: {len(tables_to_process)}")
            
            # Генерируем конфигурации для таблиц
            table_configs = []
            for table in tables_to_process:
                print(f"  Обработка: {table}")
                
                structure = pg_utils.get_table_structure(table)
                if not structure:
                    continue
                
                # Простые правила для колонок
                column_rules = {}
                for column in structure:
                    col_name = column['name']
                    
                    # Пропускаем системные колонки
                    if (pg_utils._is_generated_column(column) or 
                        pg_utils._is_auto_increment_column(column)):
                        continue
                    
                    # Базовые правила по типу данных
                    data_type = column['data_type'].lower()
                    if 'int' in data_type:
                        column_rules[col_name] = {"type": "int", "min_value": 1, "max_value": 1000}

                    elif any(num_type in data_type for num_type in ['decimal', 'numeric']):
                        column_rules[col_name] = {"type": "decimal", "min_value": 1.0, "max_value": 1000.0, "precision": 2}
                    elif 'bool' in data_type:
                        column_rules[col_name] = {"type": "boolean", "true_probability": 0.5}
                    elif 'date' in data_type:
                        column_rules[col_name] = {"type": "date", "start_date": "2023-01-01", "end_date": "2024-12-31"}
                    elif 'timestamp' in data_type:
                        column_rules[col_name] = {"type": "timestamp", "start_date": "2023-01-01 00:00:00", "end_date": "2024-12-31 23:59:59"}
                    else:
                        column_rules[col_name] = {"type": "text", "min_words": 2, "max_words": 5}
                
                table_config = {
                    "table_name": table,
                    "rows_to_generate": 100,
                    "null_probability": 0.05,
                    "unique_columns": [],
                    "column_rules": column_rules
                }
                table_configs.append(table_config)
            
            # Формируем полный конфиг
            full_config = {
                "database": minimal_config['database'],
                "tables": table_configs,
                "global_settings": minimal_config.get('global_settings', {
                    "default_null_probability": 0.05,
                    "max_retry_unique": 100,
                    "batch_size": 100,
                    "enable_foreign_keys": True,
                    "log_level": "INFO"
                })
            }
            
            # Сохраняем полный конфиг
            output_file = config_file.replace('.json', '_full.json')
            output_path = os.path.join(self.examples_dir, output_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Полный конфиг сохранен: {output_file}")
            print(f"    Сгенерировано для {len(table_configs)} таблиц")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def run(self):
        """Запускает селектор"""
        print("🚀 Селектор конфигов для генерации данных")
        
        while True:
            configs = self.show_menu()
            if not configs:
                break
            
            try:
                choice = input("\nВыберите конфиг: ").strip()
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(configs):
                    selected_config = configs[choice_num - 1]
                    self.generate_from_config(selected_config)
                elif choice_num == len(configs) + 1:
                    print("\n Конец!")
                    break
                else:
                    print("❌ Неверный выбор")
                    
            except ValueError:
                print("❌ Введите число")
            
            input("\nНажмите Enter чтобы продолжить...")

if __name__ == "__main__":
    selector = ConfigSelector()
    selector.run()