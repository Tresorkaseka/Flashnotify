"""
Tests unitaires pour les métaclasses
"""
import pytest
from core.metaclasses import NotificationMeta, ChannelMeta, NotificationRegistry


class TestNotificationMeta:
    """Tests unitaires pour NotificationMeta"""
    
    def setup_method(self):
        """Nettoie le registre avant chaque test"""
        NotificationRegistry._registry.clear()
    
    def test_creates_notification_type_attribute(self):
        """Vérifie que _notification_type est créé automatiquement"""
        
        class TestNotifier(metaclass=NotificationMeta):
            pass
        
        assert hasattr(TestNotifier, '_notification_type')
        assert TestNotifier._notification_type == 'testnotifier'
    
    def test_creates_default_description(self):
        """Vérifie que description par défaut est générée"""
        
        class CustomNotifier(metaclass=NotificationMeta):
            pass
        
        assert CustomNotifier.description == "Notificateur de type CustomNotifier"
    
    def test_respects_explicit_description(self):
        """Vérifie que description explicite n'est pas écrasée"""
        
        class CustomNotifier(metaclass=NotificationMeta):
            description = "Ma description personnalisée"
        
        assert CustomNotifier.description == "Ma description personnalisée"
    
    def test_generates_validator_from_required_fields(self):
        """Vérifie génération automatique de validate_required_fields"""
        
        class TestNotifier(metaclass=NotificationMeta):
            required_fields = ['email', 'message']
        
        assert hasattr(TestNotifier, 'validate_required_fields')
        
        instance = TestNotifier()
        instance.email = 'test@example.com'
        instance.message = 'Test message'
        
        instance.validate_required_fields()
    
    def test_validator_raises_on_missing_field(self):
        """Vérifie que le validateur lève une exception si champ manquant"""
        
        class TestNotifier(metaclass=NotificationMeta):
            required_fields = ['email', 'message']
        
        instance = TestNotifier()
        instance.email = 'test@example.com'
        
        with pytest.raises(ValueError) as exc_info:
            instance.validate_required_fields()
        
        assert 'message' in str(exc_info.value)
    
    def test_auto_registration_in_registry(self):
        """Vérifie l'enregistrement automatique dans NotificationRegistry"""
        
        class UniqueNotifier(metaclass=NotificationMeta):
            pass
        
        registered = NotificationRegistry.get('UniqueNotifier')
        assert registered is not None
        assert registered == UniqueNotifier
    
    def test_base_notifier_not_registered(self):
        """Vérifie que BaseNotifier n'est pas enregistré"""
        
        class BaseNotifier(metaclass=NotificationMeta):
            pass
        
        registered = NotificationRegistry.get('BaseNotifier')
        assert registered is None
    
    def test_inheritance_preserves_metaclass(self):
        """Vérifie que l'héritage préserve le comportement de la métaclasse"""
        
        class ParentNotifier(metaclass=NotificationMeta):
            required_fields = ['email']
        
        class ChildNotifier(ParentNotifier):
            required_fields = ['email', 'phone']
        
        assert ChildNotifier._notification_type == 'childnotifier'
        
        instance = ChildNotifier()
        instance.email = 'test@example.com'
        instance.phone = '+33612345678'
        instance.validate_required_fields()


class TestChannelMeta:
    """Tests unitaires pour ChannelMeta"""
    
    def test_generates_channel_type_from_name(self):
        """Vérifie génération automatique de channel_type"""
        
        class EmailMixin(metaclass=ChannelMeta):
            pass
        
        assert EmailMixin.channel_type == 'email'
    
    def test_strips_mixin_suffix(self):
        """Vérifie que 'Mixin' est retiré du nom"""
        
        class SMSMixin(metaclass=ChannelMeta):
            pass
        
        assert SMSMixin.channel_type == 'sms'
    
    def test_respects_explicit_channel_type(self):
        """Vérifie que channel_type explicite n'est pas écrasé"""
        
        class CustomMixin(metaclass=ChannelMeta):
            channel_type = 'custom_type'
        
        assert CustomMixin.channel_type == 'custom_type'
    
    def test_generates_get_channel_info(self):
        """Vérifie génération de get_channel_info"""
        
        class TestMixin(metaclass=ChannelMeta):
            pass
        
        instance = TestMixin()
        info = instance.get_channel_info()
        
        assert 'type' in info
        assert 'name' in info
        assert info['type'] == 'test'
        assert info['name'] == 'TestMixin'


class TestNotificationRegistry:
    """Tests pour le registre de notifications"""
    
    def setup_method(self):
        """Nettoie le registre avant chaque test"""
        NotificationRegistry._registry.clear()
    
    def test_register_and_get(self):
        """Vérifie l'enregistrement et la récupération"""
        
        class TestClass:
            pass
        
        NotificationRegistry.register('TestClass', TestClass)
        
        assert NotificationRegistry.get('TestClass') == TestClass
    
    def test_get_nonexistent_returns_none(self):
        """Vérifie que get retourne None pour une clé inexistante"""
        
        assert NotificationRegistry.get('NonExistent') is None
    
    def test_all_returns_registry(self):
        """Vérifie que all() retourne le registre complet"""
        
        class TestClass1:
            pass
        
        class TestClass2:
            pass
        
        NotificationRegistry.register('Test1', TestClass1)
        NotificationRegistry.register('Test2', TestClass2)
        
        registry = NotificationRegistry.all()
        
        assert len(registry) == 2
        assert registry['Test1'] == TestClass1
        assert registry['Test2'] == TestClass2
