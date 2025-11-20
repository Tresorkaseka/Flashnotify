"""
Métaclasses pour la génération automatique de code
"""


class NotificationRegistry:
    """Registre global des notificateurs"""
    _registry = {}
    
    @classmethod
    def register(cls, name, notifier_class):
        cls._registry[name] = notifier_class
    
    @classmethod
    def get(cls, name):
        return cls._registry.get(name)
    
    @classmethod
    def all(cls):
        return cls._registry


class NotificationMeta(type):
    """Métaclasse pour automatiser la création des notificateurs"""
    
    def __new__(cls, name, bases, attrs):
        if 'required_fields' in attrs:
            attrs['validate_required_fields'] = cls.create_validator(
                attrs['required_fields']
            )
        
        if 'description' not in attrs:
            attrs['description'] = f"Notificateur de type {name}"
        
        attrs['_notification_type'] = name.lower()
        
        new_class = super().__new__(cls, name, bases, attrs)
        
        if name != 'BaseNotifier':
            NotificationRegistry.register(name, new_class)
        
        return new_class
    
    @classmethod
    def create_validator(cls, required_fields):
        def validator(self):
            for field in required_fields:
                if getattr(self, field, None) is None:
                    raise ValueError(f"Champ requis manquant : {field}")
        return validator


class ChannelMeta(type):
    """Métaclasse pour les canaux de communication"""
    
    def __new__(cls, name, bases, attrs):
        if 'channel_type' not in attrs and name != 'BaseChannel':
            attrs['channel_type'] = name.replace('Mixin', '').lower()
        
        if 'get_channel_info' not in attrs:
            attrs['get_channel_info'] = lambda self: {
                'type': attrs.get('channel_type', 'unknown'),
                'name': name
            }
        
        return super().__new__(cls, name, bases, attrs)
