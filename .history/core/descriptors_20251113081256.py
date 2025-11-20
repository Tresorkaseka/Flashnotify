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
