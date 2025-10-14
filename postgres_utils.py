
import psycopg2
from psycopg2 import sql
import random
import string
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

class PostgresUtils:
    """Класс для работы с PostgreSQL и генерации данных"""
    
    def __init__(self, config):
        self.config = config
        self.generation_config = self._load_generation_config()
    
    def _load_generation_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию генерации из JSON файла"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return {}
    
    def get_table_config(self, table_name: str) -> Dict[str, Any]:
        """Получает конфигурацию для конкретной таблицы"""
        if 'tables' not in self.generation_config:
            return {}
        
        for table_config in self.generation_config['tables']:
            if table_config.get('table_name') == table_name:
                return table_config
        return {}
    
    def _get_days_in_month(self, year: int, month: int) -> int:
        """Возвращает количество дней в месяце с учетом високосных годов"""
        if month == 2:  # Февраль
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            else:
                return 28
        elif month in [4, 6, 9, 11]:  # Апрель, Июнь, Сентябрь, Ноябрь
            return 30
        else:  # Январь, Март, Май, Июль, Август, Октябрь, Декабрь
            return 31
    
    def _parse_date_range(self, date_str: str) -> datetime:
        """Парсит дату из строки с учетом формата"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%d.%m.%Y',
            '%d.%m.%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Если ни один формат не подошел, пробуем угадать
        try:
            return datetime.fromisoformat(date_str.replace(' ', 'T'))
        except ValueError:
            raise ValueError(f"Неизвестный формат даты: {date_str}")
    
    def _validate_date_range(self, start_date_str: str, end_date_str: str) -> tuple:
        """Проверяет и парсит диапазон дат"""
        start_date = self._parse_date_range(start_date_str)
        end_date = self._parse_date_range(end_date_str)
        
        if start_date > end_date:
            raise ValueError(f"Начальная дата {start_date} не может быть больше конечной {end_date}")
        
        return start_date, end_date
    
    def _is_generated_column(self, column_info: Dict[str, Any]) -> bool:
        """Проверяет, является ли колонка GENERATED ALWAYS"""
        # Проверяем явно указанный флаг is_generated
        if column_info.get('is_generated') == 'ALWAYS':
            return True
        
        # Проверяем наличие generation_expression
        if column_info.get('generation_expression'):
            return True
        
        # Дополнительная проверка через default значение
        if column_info.get('default') and 'GENERATED' in str(column_info.get('default', '')):
            return True
            
        return False
    
    def _is_auto_increment_column(self, column_info: Dict[str, Any]) -> bool:
        """Проверяет, является ли колонка auto-increment"""
        return column_info.get('default') and 'nextval' in str(column_info.get('default', ''))
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Получает информацию о внешних ключах таблицы"""


        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = %s
                    AND tc.table_name = %s;
                    """
                    
                    cursor.execute(query, (self.config.schema, table_name))
                    foreign_keys = cursor.fetchall()
                    
                    result = []
                    for fk in foreign_keys:
                        fk_info = {
                            'constraint_name': fk[0],
                            'column_name': fk[1],
                            'foreign_table_name': fk[2],
                            'foreign_column_name': fk[3]
                        }
                        result.append(fk_info)
                    return result
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка получения внешних ключей: {e}")
            return []

    def get_existing_foreign_keys_values(self, foreign_table_name: str, foreign_column_name: str) -> List[Any]:
        """Получает существующие значения из таблицы, на которую ссылается внешний ключ"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    query = sql.SQL("SELECT DISTINCT {} FROM {}.{} WHERE {} IS NOT NULL").format(
                        sql.Identifier(foreign_column_name),
                        sql.Identifier(self.config.schema),
                        sql.Identifier(foreign_table_name),
                        sql.Identifier(foreign_column_name)
                    )
                    
                    cursor.execute(query)
                    values = cursor.fetchall()
                    return [value[0] for value in values]
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка получения значений внешнего ключа: {e}")
            return []

    def get_all_schemas(self) -> List[str]:
        """Получаем список всех схем в базе данных"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT LIKE 'pg_%' 
                    AND schema_name != 'information_schema'
                    ORDER BY schema_name;
                    """
                    
                    cursor.execute(query)
                    schemas = cursor.fetchall()
                    return [schema[0] for schema in schemas]
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка: {e}")
            return []

    def get_all_tables(self) -> List[str]:
        """Получаем список всех таблиц в выбранной схеме"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                    
                    cursor.execute(query, (self.config.schema,))
                    tables = cursor.fetchall()
                    return [table[0] for table in tables]
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка: {e}")
            return []

    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """Получаем полную структуру таблицы"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT 
                        column_name, 
                        data_type, 
                        character_maximum_length,
                        is_nullable,
                        column_default,
                        is_generated,
                        generation_expression
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                    """
                    
                    cursor.execute(query, (self.config.schema, table_name))
                    columns = cursor.fetchall()
                    
                    structure = []
                    for col in columns:
                        column_info = {
                            'name': col[0],
                            'data_type': col[1],
                            'max_length': col[2],
                            'nullable': col[3] == 'YES',
                            'default': col[4],
                            'is_generated': col[5],
                            'generation_expression': col[6]
                        }
                        structure.append(column_info)
                    return structure
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка получения структуры: {e}")
            return []

    def display_table_structure(self, table_name: str, structure: List[Dict[str, Any]]):
        """Показывает структуру таблицы в читаемом формате"""
        print(f"\n📋 Структура таблицы '{table_name}':")
        print("-" * 80)
        print(f"{'Колонка':<20} {'Тип':<20} {'NULL':<8} {'Generated':<10} {'Default'}")
        print("-" * 80)
        
        for col in structure:
            null_info = "YES" if col['nullable'] else "NO"
            default_info = col['default'] or ""
            data_type = col['data_type']
            if col['max_length']:
                data_type += f"({col['max_length']})"
            
            generated_info = "ALWAYS" if self._is_generated_column(col) else "NO"
            if self._is_auto_increment_column(col):
                generated_info = "AUTO_INC"
            
            print(f"{col['name']:<20} {data_type:<20} {null_info:<8} {generated_info:<10} {default_info}")

    def _generate_fallback_value(self, value_type: str, rules: Dict[str, Any], existing_values: set) -> Any:
        """Генерирует запасное значение при невозможности создать уникальное"""
        if value_type == 'int':
            min_val = rules.get('min_value', 1)
            # Ищем первое свободное число
            for i in range(min_val, min_val + 10000):
                if i not in existing_values:
                    return i
        # Для остальных типов добавляем уникальный суффикс
        return f"fallback_{len(existing_values) + 1}_{random.randint(1000, 9999)}"

    def _generate_value_by_rules(self, column_name: str, rules: Dict[str, Any], existing_values: set = None) -> Any:


        """Генерирует значение по правилам из конфигурации"""
        value_type = rules.get('type', 'text')
        max_retry = self.generation_config.get('global_settings', {}).get('max_retry_unique', 100)
        
        for attempt in range(max_retry):
            try:
                if value_type == 'int':
                    min_val = rules.get('min_value', 1)
                    max_val = rules.get('max_value', 100)
                    value = random.randint(min_val, max_val)
                    
                elif value_type == 'decimal':
                    min_val = rules.get('min_value', 1.0)
                    max_val = rules.get('max_value', 1000.0)
                    precision = rules.get('precision', 2)
                    value = round(random.uniform(min_val, max_val), precision)
                    
                elif value_type == 'timestamp':
                    start_date_str = rules.get('start_date', '2020-01-01 00:00:00')
                    end_date_str = rules.get('end_date', '2024-12-31 23:59:59')
                    start_date, end_date = self._validate_date_range(start_date_str, end_date_str)
                    time_between = end_date - start_date
                    random_seconds = random.randint(0, int(time_between.total_seconds()))
                    random_date = start_date + timedelta(seconds=random_seconds)
                    value = random_date.strftime('%Y-%m-%d %H:%M:%S')
                    
                elif value_type == 'date':
                    start_date_str = rules.get('start_date', '2020-01-01')
                    end_date_str = rules.get('end_date', '2024-12-31')
                    start_date, end_date = self._validate_date_range(start_date_str, end_date_str)
                    time_between = end_date - start_date
                    random_days = random.randint(0, time_between.days)
                    random_date = start_date + timedelta(days=random_days)
                    value = random_date.strftime('%Y-%m-%d')
                    
                elif value_type == 'boolean':
                    true_probability = rules.get('true_probability', 0.5)
                    value = random.random() < true_probability
                    
                elif value_type == 'email':
                    domains = rules.get('domains', ['gmail.com', 'mail.ru', 'yandex.ru'])
                    name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
                    domain = random.choice(domains)
                    value = f"{name}{random.randint(1, 999)}@{domain}"
                    
                elif value_type == 'pattern':
                    pattern = rules.get('pattern', '#####')
                    value = ''.join(
                        random.choice(string.ascii_uppercase) if char == 'A' else
                        random.choice(string.ascii_lowercase) if char == 'a' else
                        random.choice(string.digits) if char == '#' else
                        char
                        for char in pattern
                    )
                    
                elif value_type == 'enum':
                    values = rules.get('values', ['value1', 'value2'])
                    value = random.choice(values)
                    
                else:  # text или другие типы
                    min_words = rules.get('min_words', 5)
                    max_words = rules.get('max_words', 20)
                    include_words = rules.get('include_words', [])
                    
                    words = []
                    num_words = random.randint(min_words, max_words)
                    
                    for word in include_words:
                        if len(words) < num_words:
                            words.append(word)


                    while len(words) < num_words:
                        word_length = random.randint(3, 10)
                        word = ''.join(random.choices(string.ascii_letters, k=word_length))
                        words.append(word)
                    
                    random.shuffle(words)
                    value = ' '.join(words)
                
                # ПРОВЕРКА УНИКАЛЬНОСТИ - ИСПРАВЛЕННАЯ ЛОГИКА
                if existing_values is None:
                    return value
                elif value not in existing_values:
                    return value
                    
            except Exception as e:
                print(f"❌ Ошибка генерации значения для {column_name}: {e}")
                value = f"error_{random.randint(1, 1000)}"
                if existing_values is None or value not in existing_values:
                    return value
        
        # Если не удалось сгенерировать уникальное значение
        return self._generate_fallback_value(value_type, rules, existing_values)

    def _generate_unique_value_by_rules(self, column_name: str, rules: Dict[str, Any], existing_values: set) -> Any:
        """Генерирует уникальное значение по правилам с проверкой уникальности"""
        return self._generate_value_by_rules(column_name, rules, existing_values)

    def _generate_column_value(self, column_name: str, data_type: str, max_length: int = None):
        """Генерирует значение для конкретной колонки (резервный метод)"""
        
        first_names = ['Ivan', 'Petr', 'Maria', 'Anna', 'Sergey', 'Olga', 'Alexey', 'Elena']
        last_names = ['Ivanov', 'Petrov', 'Sidorov', 'Smirnov', 'Kuznetsov', 'Popov']
        cities = ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg', 'Kazan']
        
        if 'int' in data_type:
            return random.randint(1, 1000)
        elif 'varchar' in data_type or 'text' in data_type:
            max_len = max_length or 50
            
            # Определяем тип данных по имени колонки
            if 'name' in column_name.lower() and 'last' not in column_name.lower():
                value = random.choice(first_names)
            elif 'last' in column_name.lower() or 'surname' in column_name.lower():
                value = random.choice(last_names)
            elif 'email' in column_name.lower():
                name = random.choice(first_names).lower()
                domain = random.choice(['gmail.com', 'mail.ru', 'yandex.ru'])
                value = f"{name}{random.randint(1, 999)}@{domain}"
            elif 'city' in column_name.lower() or 'address' in column_name.lower():
                value = random.choice(cities)
            else:
                # Генерируем случайную строку
                length = random.randint(5, min(20, max_len))
                value = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            
            # Обрезаем если превышает длину
            if len(value) > max_len:
                value = value[:max_len]
            return value
            
        elif 'bool' in data_type:
            return random.choice([True, False])
        elif 'date' in data_type:
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            day = random.randint(1, self._get_days_in_month(year, month))
            return f"{year}-{month:02d}-{day:02d}"
        elif 'timestamp' in data_type:
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            day = random.randint(1, self._get_days_in_month(year, month))
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
        elif 'decimal' in data_type or 'numeric' in data_type:
            return round(random.uniform(1, 1000), 2)
        else:
            return f"data_{random.randint(1, 1000)}"


    def _generate_unique_simple_value(self, column_name: str, data_type: str, max_length: int, existing_values: set, max_attempts: int):
        """Генерирует уникальное простое значение (без рекурсии)"""
        for _ in range(max_attempts):
            value = self._generate_column_value(column_name, data_type, max_length)
            if value not in existing_values:
                return value
        # Fallback
        base_value = self._generate_column_value(column_name, data_type, max_length - 5 if max_length else None)
        suffix = random.randint(1000, 9999)
        return f"{base_value}_{suffix}" if isinstance(base_value, str) else base_value * 1000 + suffix

    def generate_synthetic_data(self, table_name: str, structure: List[Dict[str, Any]], num_rows: int, existing_fk_values: Dict[str, List[Any]] = None) -> List[Dict[str, Any]]:
        """Генерирует синтетические данные с учетом внешних ключей"""
        
        table_config = self.get_table_config(table_name)
        if not table_config:
            print(f"❌ Конфигурация для таблицы '{table_name}' не найдена")
            return []
        
        null_probability = table_config.get('null_probability', 
                                        self.generation_config.get('global_settings', {}).get('default_null_probability', 0.1))
        unique_columns = table_config.get('unique_columns', [])
        column_rules = table_config.get('column_rules', {})
        
        # Получаем информацию о внешних ключах
        foreign_keys = self.get_foreign_keys(table_name)
        
        synthetic_data = []
        generated_values = {col: set() for col in unique_columns}
        
        # ФИЛЬТРУЕМ КОЛОНКИ: исключаем GENERATED ALWAYS и auto-increment
        filtered_columns = []
        for column in structure:
            if self._is_generated_column(column):
                print(f"⚠️  Пропуск GENERATED ALWAYS колонки: {column['name']}")
                continue
            if self._is_auto_increment_column(column):
                print(f"⚠️  Пропуск auto-increment колонки: {column['name']}")
                continue
            filtered_columns.append(column)
        
        print(f"🔄 Генерация {num_rows} строк для {len(filtered_columns)} колонок...")
        
        for row_num in range(num_rows):
            row_data = {}
            
            for column in filtered_columns:
                column_name = column['name']
                data_type = column['data_type'].lower()
                
                # Проверяем, является ли колонка внешним ключом
                fk_info = next((fk for fk in foreign_keys if fk['column_name'] == column_name), None)
                
                # Генерируем NULL с заданной вероятностью для nullable полей
                if column['nullable'] and random.random() < null_probability:
                    row_data[column_name] = None
                    continue
                
                # Если это внешний ключ, используем существующие значения
                if fk_info and existing_fk_values:
                    foreign_key = f"{fk_info['foreign_table_name']}.{fk_info['foreign_column_name']}"
                    if foreign_key in existing_fk_values and existing_fk_values[foreign_key]:
                        value = random.choice(existing_fk_values[foreign_key])
                        row_data[column_name] = value
                        continue
                
                # Генерируем значение по правилам из конфига или по умолчанию
                if column_name in column_rules:
                    if column_name in unique_columns:
                        value = self._generate_unique_value_by_rules(
                            column_name, column_rules[column_name], generated_values[column_name])
                        generated_values[column_name].add(value)
                    else:
                        value = self._generate_value_by_rules(column_name, column_rules[column_name])
                else:
                    # Генерируем уникальные значения для указанных колонок
                    if column_name in unique_columns:
                        value = self._generate_unique_simple_value(
                            column_name, data_type, column['max_length'], generated_values[column_name], 1000
                        )
                        generated_values[column_name].add(value)
                    else:
                        value = self._generate_column_value(column_name, data_type, column['max_length'])
                
                row_data[column_name] = value
            
            synthetic_data.append(row_data)
            
            if (row_num + 1) % 100 == 0 or (row_num + 1) == num_rows:
                print(f"✅ Сгенерировано {row_num + 1} строк...")
        
        return synthetic_data

    def insert_synthetic_data(self, table_name: str, synthetic_data: List[Dict[str, Any]]) -> bool:
        """Вставляет синтетические данные в таблицу"""
        if not synthetic_data:
            print("❌ Нет данных для вставки")
            return False
        
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    # Создаем SQL запрос для вставки
                    columns = list(synthetic_data[0].keys())
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join(columns)
                    
                    # Безопасное формирование запроса
                    query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                        sql.Identifier(self.config.schema),
                        sql.Identifier(table_name),
                        sql.SQL(columns_str),
                        sql.SQL(placeholders)
                    )
                    
                    # Подготавливаем данные для вставки
                    data_to_insert = [tuple(row[col] for col in columns) for row in synthetic_data]
                    
                    # Вставляем данные
                    cursor.executemany(query, data_to_insert)
                    conn.commit()
                    
                    print(f"✅ Успешно вставлено {len(synthetic_data)} строк в таблицу {table_name}")
                    return True
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка при вставке данных: {e}")
            return False

    def insert_data_with_fk_handling(self, table_name: str, num_rows: int) -> bool:
        """Вставляет данные с автоматической обработкой внешних ключей"""
        
        # Получаем структуру таблицы
        structure = self.get_table_structure(table_name)
        if not structure:
            print(f"❌ Не удалось получить структуру таблицы {table_name}")
            return False
        
        # Получаем внешние ключи
        foreign_keys = self.get_foreign_keys(table_name)
        
        # Собираем существующие значения для внешних ключей
        existing_fk_values = {}
        for fk in foreign_keys:
            foreign_key = f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
            print(f"🔍 Получение значений для внешнего ключа: {foreign_key}")
            values = self.get_existing_foreign_keys_values(fk['foreign_table_name'], fk['foreign_column_name'])
            existing_fk_values[foreign_key] = values
            print(f"📊 Найдено {len(values)} существующих значений")
        
        # Генерируем данные с учетом внешних ключей


        synthetic_data = self.generate_synthetic_data(table_name, structure, num_rows, existing_fk_values)
        
        if not synthetic_data:
            print(f"❌ Не удалось сгенерировать данные для таблицы {table_name}")
            return False
        
        # Вставляем данные
        return self.insert_synthetic_data(table_name, synthetic_data)

    def validate_foreign_keys(self, table_name: str, synthetic_data: List[Dict[str, Any]]) -> bool:
        """Проверяет, что все внешние ключи в данных существуют"""
        foreign_keys = self.get_foreign_keys(table_name)
        
        for fk in foreign_keys:
            column_name = fk['column_name']
            foreign_table = fk['foreign_table_name']
            foreign_column = fk['foreign_column_name']
            
            # Получаем существующие значения
            existing_values = self.get_existing_foreign_keys_values(foreign_table, foreign_column)
            
            # Проверяем все значения в данных
            for row in synthetic_data:
                if column_name in row and row[column_name] is not None:
                    if row[column_name] not in existing_values:
                        print(f"❌ Нарушение внешнего ключа: {row[column_name]} не найден в {foreign_table}.{foreign_column}")
                        return False
        
        return True

    def test_connection(self) -> bool:
        """Проверяет подключение к базе данных"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                return True
        except psycopg2.Error as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def get_advanced_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """Расширенный метод получения структуры с надежным определением GENERATED колонок"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    # Запрос к системным таблицам PostgreSQL для надежного определения
                    query = """
                    SELECT 
                        a.attname as column_name,
                        format_type(a.atttypid, a.atttypmod) as data_type,
                        CASE WHEN a.atttypmod > 0 THEN a.atttypmod - 4 ELSE NULL END as max_length,
                        CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END as is_nullable,
                        pg_get_expr(ad.adbin, ad.adrelid) as column_default,
                        a.attgenerated as is_generated
                    FROM pg_attribute a
                    LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
                    WHERE a.attrelid = %s::regclass
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    ORDER BY a.attnum;
                    """
                    
                    full_table_name = f"{self.config.schema}.{table_name}"
                    cursor.execute(query, (full_table_name,))
                    columns = cursor.fetchall()
                    
                    structure = []
                    for col in columns:
                        column_info = {
                            'name': col[0],
                            'data_type': col[1],
                            'max_length': col[2],
                            'nullable': col[3] == 'YES',
                            'default': col[4],
                            'is_generated': 'ALWAYS' if col[5] == 's' else 'NEVER'
                        }
                        structure.append(column_info)
                    return structure
                    
        except psycopg2.Error as e:
            print(f"❌ Ошибка получения расширенной структуры: {e}")
            # Fallback к базовому методу
            return self.get_table_structure(table_name)
    
    def _collect_generated_fk_values(self, table_name: str, existing_fk_values: Dict[str, List[Any]]):
        """Собирает значения из сгенерированной таблицы для использования как внешние ключи"""
        try:
            with psycopg2.connect(**self.config.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    # Получаем структуру таблицы чтобы определить первичные ключи
                    structure = self.get_table_structure(table_name)
                    
                    for column in structure:
                        # Предполагаем, что первичные ключи имеют имена вида id, table_id, etc.
                        if column['name'] in ['id', f'{table_name}_id', 'user_id', 'order_id']:
                            query = sql.SQL("SELECT DISTINCT {} FROM {}.{}").format(
                                sql.Identifier(column['name']),
                                sql.Identifier(self.config.schema),
                                sql.Identifier(table_name)
                            )
                            
                            cursor.execute(query)
                            values = [row[0] for row in cursor.fetchall()]
                            
                            fk_key = f"{table_name}.{column['name']}"
                            existing_fk_values[fk_key] = values
                            print(f"📊 Сохранено {len(values)} значений для внешнего ключа: {fk_key}")
                            
        except psycopg2.Error as e:
            print(f"❌ Ошибка при сборе значений FK: {e}")