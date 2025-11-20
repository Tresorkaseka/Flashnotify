import re


class EmailDescriptor:
    """Descripteur réutilisable pour la validation d'emails"""
    
    def __init__(self):
        self._values = {}
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._values.get(id(instance))
    
    def __set__(self, instance, value):
        if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError(f"Email invalide : {value}")
        self._values[id(instance)] = value
    
    def __delete__(self, instance):
        if id(instance) in self._values:
            del self._values[id(instance)]


class PhoneDescriptor:
    """Descripteur pour la validation des numéros internationaux"""
    
    def __init__(self):
        self._values = {}
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._values.get(id(instance))
    
    def __set__(self, instance, value):
        if value and not self.validate_international_phone(value):
            raise ValueError(f"Numéro de téléphone invalide : {value}")
        self._values[id(instance)] = value
    
    def __delete__(self, instance):
        if id(instance) in self._values:
            del self._values[id(instance)]
    
    @staticmethod
    def validate_international_phone(phone):
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))


class PriorityDescriptor:
    """Descripteur pour contrôler les niveaux de priorité"""
    
    VALID_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    def __init__(self):
        self._values = {}
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._values.get(id(instance), 'MEDIUM')
    
    def __set__(self, instance, value):
        if value and value.upper() not in self.VALID_PRIORITIES:
            raise ValueError(f"Priorité invalide : {value}. Valeurs acceptées : {self.VALID_PRIORITIES}")
        self._values[id(instance)] = value.upper() if value else 'MEDIUM'
    
    def __delete__(self, instance):
        if id(instance) in self._values:
            del self._values[id(instance)]


class TimeWindowDescriptor:
    """Descripteur pour la validation des plages horaires"""
    
    def __init__(self, start_hour=9, end_hour=17):
        self._values = {}
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._values.get(id(instance))
    
    def __set__(self, instance, value):
        if value is None:
            self._values[id(instance)] = value
            return
        
        if isinstance(value, dict):
            start_time = value.get('start')
            end_time = value.get('end')
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            start_time, end_time = value
        else:
            raise ValueError(f"Format de plage horaire invalide : {value}")
        
        if not self._validate_time_format(start_time):
            raise ValueError(f"Heure de début invalide : {start_time}. Format attendu : 'HH:MM'")
        
        if not self._validate_time_format(end_time):
            raise ValueError(f"Heure de fin invalide : {end_time}. Format attendu : 'HH:MM'")
        
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        if start_hour < 0 or start_hour > 23 or end_hour < 0 or end_hour > 23:
            raise ValueError("Les heures doivent être comprises entre 00 et 23")
        
        if start_minute < 0 or start_minute > 59 or end_minute < 0 or end_minute > 59:
            raise ValueError("Les minutes doivent être comprises entre 00 et 59")
        
        self._values[id(instance)] = {
            'start': start_time,
            'end': end_time,
            'start_hour': start_hour,
            'start_minute': start_minute,
            'end_hour': end_hour,
            'end_minute': end_minute
        }
    
    def __delete__(self, instance):
        if id(instance) in self._values:
            del self._values[id(instance)]
    
    @staticmethod
    def _validate_time_format(time_str):
        """Valide le format HH:MM"""
        if not isinstance(time_str, str):
            return False
        
        import re
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return bool(re.match(pattern, time_str))
    
    def is_in_window(self, instance, check_time=None):
        """Vérifie si l'heure actuelle est dans la plage définie"""
        import datetime
        
        if check_time is None:
            check_time = datetime.datetime.now()
        elif isinstance(check_time, str):
            try:
                hour, minute = map(int, check_time.split(':'))
                check_time = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                raise ValueError(f"Format d'heure invalide : {check_time}")
        
        window_config = self._values.get(id(instance))
        if not window_config:
            return True  # Aucune restriction si non configuré
        
        current_time = check_time.time()
        start_time = datetime.time(window_config['start_hour'], window_config['start_minute'])
        end_time = datetime.time(window_config['end_hour'], window_config['end_minute'])
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Plage chevauchant minuit
            return current_time >= start_time or current_time <= end_time
