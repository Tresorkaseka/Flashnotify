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


class TemplateMeta(type):
    """Métaclasse pour les templates de messages"""
    
    def __new__(cls, name, bases, attrs):
        if 'template_version' not in attrs:
            attrs['template_version'] = '1.0.0'
        
        if 'required_variables' not in attrs:
            attrs['required_variables'] = []
        
        if 'render_template' not in attrs:
            def render_template(self, context=None):
                """Méthode de rendu de template par défaut"""
                template_content = getattr(self, 'content', '')
                context = context or {}
                
                # Remplacement des variables requises
                for var in self.required_variables:
                    if var not in context:
                        raise ValueError(f"Variable requise manquante : {var}")
                    template_content = template_content.replace(f"{{{{{var}}}}}", str(context[var]))
                
                # Remplacement des variables optionnelles
                for key, value in context.items():
                    template_content = template_content.replace(f"{{{{{key}}}}}", str(value))
                
                return template_content
            
            attrs['render_template'] = render_template
        
        # Enregistrement automatique dans le registre des templates
        if name != 'BaseTemplate':
            NotificationRegistry.register(f"template_{name.lower()}", cls)
        
        return super().__new__(cls, name, bases, attrs)


class ConfigMeta(type):
    """Métaclasse pour la configuration dynamique"""
    
    _config_instances = {}
    
    def __new__(cls, name, bases, attrs):
        # Ajout des méthodes de gestion de configuration
        if 'get_config' not in attrs:
            def get_config(self, key, default=None):
                """Récupère une valeur de configuration"""
                return getattr(self, '_config', {}).get(key, default)
            
            attrs['get_config'] = get_config
        
        if 'set_config' not in attrs:
            def set_config(self, key, value):
                """Définit une valeur de configuration"""
                if not hasattr(self, '_config'):
                    self._config = {}
                self._config[key] = value
            
            attrs['set_config'] = set_config
        
        if 'load_from_dict' not in attrs:
            def load_from_dict(self, config_dict):
                """Charge la configuration depuis un dictionnaire"""
                if not hasattr(self, '_config'):
                    self._config = {}
                self._config.update(config_dict)
            
            attrs['load_from_dict'] = load_from_dict
        
        if 'validate_config' not in attrs:
            def validate_config(self):
                """Valide la configuration (à surcharger)"""
                required_fields = getattr(self, 'required_config_fields', [])
                for field in required_fields:
                    if field not in self._config:
                        raise ValueError(f"Champ de configuration requis manquant : {field}")
                return True
            
            attrs['validate_config'] = validate_config
        
        # Enregistrement pour le singleton
        if name != 'BaseConfig':
            cls._config_instances[name] = None
        
        return super().__new__(cls, name, bases, attrs)
    
    def __call__(cls, *args, **kwargs):
        """Implémente le pattern Singleton pour les configurations"""
        if cls.__name__ != 'BaseConfig' and cls.__name__ in cls._config_instances:
            if cls._config_instances[cls.__name__] is None:
                instance = super().__call__(*args, **kwargs)
                cls._config_instances[cls.__name__] = instance
                return instance
            else:
                return cls._config_instances[cls.__name__]
        else:
            return super().__call__(*args, **kwargs)
