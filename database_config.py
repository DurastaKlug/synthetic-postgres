import json

class DatabaseConfig:
    """Конфигурация подключения к PostgreSQL"""
    
    def __init__(self, **kwargs):
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 5432)
        self.database = kwargs.get('database', 'postgres')
        self.user = kwargs.get('user', 'postgres')
        self.password = kwargs.get('password', '')
        self.schema = kwargs.get('schema', 'public')
    
    def get_connection_params(self) -> dict:
        """Возвращает параметры подключения в виде словаря"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
    
    @classmethod
    def from_json(cls, config_file: str = 'config.json'):
        """Создает конфигурацию из JSON файла"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            db_config = config_data.get('database', {})
            return cls(**db_config)
            
        except FileNotFoundError:
            print(f"❌ Файл конфигурации {config_file} не найден")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка чтения JSON: {e}")
            return None
    
    def str(self) -> str:
        """Строковое представление конфига (без пароля)"""
        return (f"DatabaseConfig(host='{self.host}', port={self.port}, "
                f"database='{self.database}', user='{self.user}', schema='{self.schema}')")