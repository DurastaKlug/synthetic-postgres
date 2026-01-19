- [ENGL Synthetic Data Generator for PostgreSQL](#engl-synthetic-data-generator-for-postgresql)
  - [Features](#features)
  - [Supported Data Types](#supported-data-types)
  - [Quick Start](#quick-start)
    - [1. Environment Setup and Installation](#1-environment-setup-and-installation)
- [Create a virtual environment](#create-a-virtual-environment)
- [Activate (Windows)](#activate-windows)
- [Activate (Mac/Linux)](#activate-maclinux)
- [Install dependencies](#install-dependencies)
    - [2. Visual Studio Code Setup (Recommended)](#2-visual-studio-code-setup-recommended)
    - [3. JSON Configuration Setup](#3-json-configuration-setup)
- [Copy the suitable template to the project root as config.json](#copy-the-suitable-template-to-the-project-root-as-configjson)
    - [4. Configuration File Structure](#4-configuration-file-structure)
      - [Database Connection Settings](#database-connection-settings)
      - [Table Settings](#table-settings)
      - [Column Generation Rules (`column_rules`)](#column-generation-rules-column_rules)
      - [Global Settings (`global_settings`)](#global-settings-global_settings)
    - [5. Running the Generator](#5-running-the-generator)
  - [📁 Project Structure](#-project-structure)
  - [✅ Important Notes and Troubleshooting](#-important-notes-and-troubleshooting)
- [RU Генератор синтетических данных для PostgreSQL](#ru-генератор-синтетических-данных-для-postgresql)
  - [Возможности](#возможности)
  - [Поддерживаемые типы данных](#поддерживаемые-типы-данных)
  - [Быстрый старт](#быстрый-старт)
    - [1. Установка и настройка окружения](#1-установка-и-настройка-окружения)
- [Активация (Windows)](#активация-windows)
- [Активация (Mac/Linux)](#активация-maclinux)
    - [2. Следующая настройка под Visual Studio Code (оптимально)](#2-следующая-настройка-под-visual-studio-code-оптимально)
    - [3. Настройка конфигурации JSON](#3-настройка-конфигурации-json)
- [Скопируйте подходящий шаблон в корень проекта как config.json](#скопируйте-подходящий-шаблон-в-корень-проекта-как-configjson)
    - [4. Конфигурация файловой структуры](#4-конфигурация-файловой-структуры)
- [Настройки таблиц](#настройки-таблиц)
- [Правила для колонок](#правила-для-колонок)
    - [Глобальные настройки](#глобальные-настройки)
    - [5. Запуск генератора](#5-запуск-генератора)
  - [📁 Пример структуры проекта:](#-пример-структуры-проекта)
  - [✅ Важные рекомендации и устранение неполадок](#-важные-рекомендации-и-устранение-неполадок)


# ENGL Synthetic Data Generator for PostgreSQL

A professional tool for generating realistic synthetic data into PostgreSQL databases. 
Supports flexible generation rule configuration via JSON files.

## Features

- **Database Structure Analysis** - Automatic retrieval of table lists and their structure.
- **Smart Data Generation** - Support for a wide range of PostgreSQL data types.
- **Flexible Configuration** - Fine-tuning rules through JSON files.
- **Unique Values** - Guaranteed uniqueness for specified columns.
- **Date Ranges** - Generation of timestamps within specified intervals.
- **Typed Generation** - Intelligent data type detection based on column names.

## Supported Data Types

- Integer (`int`, `bigint`, `serial`)
- String (`varchar`, `text`)
- Boolean (`boolean`)
- Dates and timestamps (`date`, `timestamp`)
- Floating-point numbers (`decimal`, `numeric`)
- Email addresses
- Enumerations (`enum`)
- Pattern-based

## Quick Start

### 1. Environment Setup and Installation

# Create a virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


### 2. Visual Studio Code Setup (Recommended)

1. Press `Ctrl+Shift+P` to open the command palette.
2. Type: **Python: Select Interpreter**
3. Select the interpreter: `.\venv\Scripts\python.exe`

### 3. JSON Configuration Setup

Ready-made configuration templates are located in the generator_config_json/examples/ folder:

only_schema.json - Generate data for all tables in the specified schema. 
When to Use: For complete database schema population.
schema_with_tables_config.json - Generate data for specific tables in a schema. 
When to Use: For selective table population.

**How to use a template:**

# Copy the suitable template to the project root as config.json
cp generator_config_json/examples/only_schema.json config.json

Edit config.json for your database.

### 4. Configuration File Structure

#### Database Connection Settings

{
  "host": "localhost",
  "port": 5432,
  "database": "your_database",
  "user": "your_username",
  "password": "your_password",
  "schema": "public"
}


#### Table Settings
*   `table_name` - Table name.
*   `rows_to_generate` - Number of rows to generate.
*   `null_probability` - Probability of a NULL value (0.0 to 1.0).
*   `unique_columns` - List of columns requiring unique values.

#### Column Generation Rules (`column_rules`)
| Type (`type`) | Description | Key Parameters |
| **`"int"`** | Integer number. | `min_value`, `max_value` |
| **`"decimal"`** | Decimal number. | `precision` |
| **`"text"`** | Text. | `min_words`, `max_words` |
| **`"email"`** | Email address. | `domains` |
| **`"boolean"`** | Boolean value. | `true_probability` |
| **`"date"`/`"timestamp"`** | Date/time. | `start_date`, `end_date` |
| **`"pattern"`** | Pattern-based. | `pattern` (e.g., `"A##-B###"`) |
| **`"enum"`** | Value from a list. | `values` |

#### Global Settings (`global_settings`)
*   `default_null_probability` - Default NULL probability (e.g., `0.05`).
*   `max_retry_unique` - Number of attempts to generate a unique value (default `1000`).
*   `batch_size` - Number of rows for batch insertion (recommended `100`).
*   `enable_foreign_keys` - Foreign key constraint check (`true`/`false`).
*   `log_level` - Logging detail level (`"INFO"` or `"DEBUG"`).


### 5. Running the Generator

python main.py

After launch, the generator will:
1.  Analyze the structure of your PostgreSQL database.
2.  Apply generation rules from the `config.json` file.
3.  Generate and insert synthetic data in batches.
4.  Check referential integrity between tables (if enabled).



## 📁 Project Structure

├── main.py                    # Main executable script
├── postgres_utils.py          # PostgreSQL interaction logic
├── database_config.py         # Connection settings management
├── config.json                # Your configuration file (created from a template)
├── generator_config_json/     # Configuration templates
│   └── examples/
│       ├── only_schema.json
│       └── schema_with_tables_config.json
├── example-create_table.sql   # Example SQL scripts for table creation
└── requirements.txt           # Python dependencies list


## ✅ Important Notes and Troubleshooting

**Work Order:**
1.  **Fill tables in the correct order**: Start with tables referenced by others (parent tables), then child tables.
2.  **String types**: For `varchar` or `bpchar` columns, specify `type: "text"` in the config.

**Performance Tuning:**
*   Increase the **`batch_size`** parameter to `200-1000` when working with large tables.
*   For unique values, ensure the range (`min_value`/`max_value`) is sufficient to generate the required number of rows.

**Troubleshooting:**
*   **Foreign Key Error**: Check the order of tables in `config.json`. Tables should be listed from parent to child.
*   **Detailed Logging**: For non-obvious errors, change `log_level` to `"DEBUG"` in the configuration for a detailed report.
*   **Test Run**: Always test your configuration with a small amount of data (`rows_to_generate: 5-10`) before running a full generation.

# RU Генератор синтетических данных для PostgreSQL

Профессиональный инструмент для генерации реалистичных синтетических данных в базы данных PostgreSQL. 
Поддерживает гибкую настройку правил генерации через JSON-конфигурацию.

## Возможности

- **Анализ структуры БД** - автоматическое получение списка таблиц и их структуры.
- **Умная генерация данных** - поддержка широкого спектра типов данных PostgreSQL.
- **Гибкая конфигурация** - тонкая настройка правил через JSON-файлы.
- **Уникальные значения** - гарантия уникальности для указанных колонок.
- **Диапазоны дат** - генерация временных меток в заданных промежутках.
- **Типизированная генерация** - интеллектуальное определение типа данных по имени колонки.

## Поддерживаемые типы данных

- Целочисленные (`int`, `bigint`, `serial`)
- Строковые (`varchar`, `text`)
- Булевы (`boolean`)
- Даты и временные метки (`date`, `timestamp`)
- Числа с плавающей точкой (`decimal`, `numeric`)
- Email-адреса
- Перечисления (`enum`)
- Шаблоны (`pattern-based`)

## Быстрый старт

### 1. Установка и настройка окружения

 Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Mac/Linux)
source venv/bin/activate

 Установка зависимостей
pip install -r requirements.txt

### 2. Следующая настройка под Visual Studio Code (оптимально)
   
vs code горячие клавиши: Ctrl+Shift+P
vs code поисковик: Python: Select Interpretator
-> .\venv\Scripts\python.exe

### 3. Настройка конфигурации JSON

	Шаблоны

only_schema.json - Генерация данных для всех таблиц в указанной схеме.	
Когда используется: Для полного заполнения схемы БД.

schema_with_tables_config.json - Генерация данных для конкретных таблиц в схеме.	
Когда используется: Для выборочного заполнения таблиц.

Как использовать шаблон: 

# Скопируйте подходящий шаблон в корень проекта как config.json
cp generator_config_json/examples/only_schema.json config.json

Отредактируйте config.json под вашу базу данных.

### 4. Конфигурация файловой структуры
Настройки подключения к базе данных

{
  "host": "localhost",
  "port": 5432,
  "database": "ваша_база",
  "user": "ваш_пользователь",
  "password": "ваш_пароль",
  "schema": "public"
}

# Настройки таблиц

table_name - имя таблицы
rows_to_generate - сколько строк создать
null_probability - шанс NULL (0.0-1.0)
unique_columns - список колонок с уникальными значениями

# Правила для колонок

type - тип данных:

· "int" - числа (min_value/max_value)
· "decimal" - дробные числа (precision)
· "text" - текст (min_words/max_words)
· "email" - email (domains)
· "boolean" - true/false (true_probability)
· "date/timestamp" - даты (start_date/end_date)
· "pattern" - по шаблону (#-цифры, A-буквы)
· "enum" - из списка (values)

### Глобальные настройки

default_null_probability - шанс NULL по умолчанию
max_retry_unique- попытки для уникальных значений
batch_size- размер пачки вставки
enable_foreign_keys- проверка связей между таблицами

default_null_probability - шанс NULL по умолчанию (0.05 = 5%)
max_retry_unique - попытки создать уникальное значение (1000)
date_format - формат дат (YYYY-MM-DD)
timestamp_format - формат времени (YYYY-MM-DD HH:MI:SS)
batch_size - строк за одну вставку, индивидуальное количество в зависимости от таблицы! (100)
enable_foreign_keys - проверка связей между таблицами (true), отвечает за PK и FK
log_level - детальность логов (INFO - стандартное, DEBUG - подробно)

### 5. Запуск генератора
python main.py

**Важно!**
· Сначала заполняйте таблицы, на которые ссылаются другие
· Для varchar/bpchar используйте type: "text"
· Уникальные значения требуют достаточного диапазона

## 📁 Пример структуры проекта:
├── main.py                    # Основной исполняемый скрипт
├── postgres_utils.py          # Логика взаимодействия с PostgreSQL
├── database_config.py         # Управление настройками подключения
├── config.json                # Ваш файл конфигурации (создается из шаблона)
├── generator_config_json/     # Шаблоны конфигурации
│   └── examples/
│       ├── only_schema.json
│       └── schema_with_tables_config.json
├── example-create_table.sql   # Пример SQL-скриптов для создания таблиц
└── requirements.txt           # Список зависимостей Python

## ✅ Важные рекомендации и устранение неполадок

**Порядок работы:**
1.  **Заполняйте таблицы в правильном порядке**: начните с таблиц, на которые ссылаются другие (родительские таблицы), затем переходите к дочерним.
2.  **Строковые типы данных**: для колонок типа `varchar` или `bpchar` указывайте `type: "text"` в конфигурации.

**Настройка производительности:**
*   **Увеличьте параметр `batch_size`** до `200-1000` при работе с большими таблицами.
*   Для **уникальных значений** убедитесь, что заданный диапазон (`min_value`/`max_value`) достаточен для генерации необходимого количества строк.

**Диагностика проблем:**
*   **Ошибка внешнего ключа (Foreign Key Error)**: проверьте порядок таблиц в файле `config.json`. Таблицы должны быть перечислены в порядке от родительских к дочерним.
*   **Подробное логирование**: при возникновении неочевидных ошибок измените `log_level` на `"DEBUG"` в конфигурации для получения детального отчета.
*   **Пробный запуск**: всегда тестируйте конфигурацию на небольшом объёме данных (например, `rows_to_generate: 5-10`), прежде чем запускать полную генерацию.






