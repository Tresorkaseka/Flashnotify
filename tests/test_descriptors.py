"""
Tests unitaires pour les descripteurs
"""
import pytest
from core.descriptors import EmailDescriptor, PhoneDescriptor, PriorityDescriptor


class TestEmailDescriptor:
    """Tests pour EmailDescriptor"""
    
    def test_valid_email(self):
        """Vérifie qu'un email valide est accepté"""
        
        class TestClass:
            email = EmailDescriptor()
        
        instance = TestClass()
        instance.email = 'test@example.com'
        
        assert instance.email == 'test@example.com'
    
    def test_invalid_email_raises_valueerror(self):
        """Vérifie qu'un email invalide lève ValueError"""
        
        class TestClass:
            email = EmailDescriptor()
        
        instance = TestClass()
        
        with pytest.raises(ValueError) as exc_info:
            instance.email = 'invalid-email'
        
        assert 'Email invalide' in str(exc_info.value)
    
    def test_multiple_instances_independent(self):
        """Vérifie l'indépendance des instances"""
        
        class TestClass:
            email = EmailDescriptor()
        
        instance1 = TestClass()
        instance2 = TestClass()
        
        instance1.email = 'test1@example.com'
        instance2.email = 'test2@example.com'
        
        assert instance1.email == 'test1@example.com'
        assert instance2.email == 'test2@example.com'
    
    def test_none_value_allowed(self):
        """Vérifie que None est accepté"""
        
        class TestClass:
            email = EmailDescriptor()
        
        instance = TestClass()
        instance.email = None
        
        assert instance.email is None
    
    def test_various_valid_email_formats(self):
        """Vérifie différents formats d'email valides"""
        
        class TestClass:
            email = EmailDescriptor()
        
        instance = TestClass()
        
        valid_emails = [
            'simple@example.com',
            'very.common@example.com',
            'disposable.style.email.with+symbol@example.com',
            'user@localhost.localdomain',
            'user123@test-domain.co.uk'
        ]
        
        for email in valid_emails:
            instance.email = email
            assert instance.email == email


class TestPhoneDescriptor:
    """Tests pour PhoneDescriptor"""
    
    def test_valid_international_phone(self):
        """Vérifie qu'un numéro international valide est accepté"""
        
        class TestClass:
            phone = PhoneDescriptor()
        
        instance = TestClass()
        instance.phone = '+33612345678'
        
        assert instance.phone == '+33612345678'
    
    def test_invalid_phone_raises_valueerror(self):
        """Vérifie qu'un numéro invalide lève ValueError"""
        
        class TestClass:
            phone = PhoneDescriptor()
        
        instance = TestClass()
        
        with pytest.raises(ValueError) as exc_info:
            instance.phone = '123'
        
        assert 'Numéro de téléphone invalide' in str(exc_info.value)
    
    def test_validate_international_phone_method(self):
        """Vérifie la méthode de validation"""
        
        descriptor = PhoneDescriptor()
        
        assert descriptor.validate_international_phone('+33612345678')
        assert descriptor.validate_international_phone('+14155552671')
        assert not descriptor.validate_international_phone('invalid')
        assert not descriptor.validate_international_phone('123')
    
    def test_none_value_allowed(self):
        """Vérifie que None est accepté"""
        
        class TestClass:
            phone = PhoneDescriptor()
        
        instance = TestClass()
        instance.phone = None
        
        assert instance.phone is None
    
    def test_various_valid_phone_formats(self):
        """Vérifie différents formats de numéro valides"""
        
        class TestClass:
            phone = PhoneDescriptor()
        
        instance = TestClass()
        
        valid_phones = [
            '+33612345678',
            '+14155552671',
            '+861012345678',
            '+442071838750',
            '33612345678'
        ]
        
        for phone in valid_phones:
            instance.phone = phone
            assert instance.phone == phone


class TestPriorityDescriptor:
    """Tests pour PriorityDescriptor"""
    
    def test_valid_priority(self):
        """Vérifie qu'une priorité valide est acceptée"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        instance.priority = 'HIGH'
        
        assert instance.priority == 'HIGH'
    
    def test_priority_normalized_to_uppercase(self):
        """Vérifie que la priorité est normalisée en majuscules"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        instance.priority = 'low'
        
        assert instance.priority == 'LOW'
    
    def test_invalid_priority_raises_valueerror(self):
        """Vérifie qu'une priorité invalide lève ValueError"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        
        with pytest.raises(ValueError) as exc_info:
            instance.priority = 'INVALID'
        
        assert 'Priorité invalide' in str(exc_info.value)
    
    def test_default_value_is_medium(self):
        """Vérifie que la valeur par défaut est MEDIUM"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        
        assert instance.priority == 'MEDIUM'
    
    def test_all_valid_priorities(self):
        """Vérifie toutes les priorités valides"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for priority in valid_priorities:
            instance.priority = priority
            assert instance.priority == priority
    
    def test_none_value_defaults_to_medium(self):
        """Vérifie que None donne la valeur par défaut"""
        
        class TestClass:
            priority = PriorityDescriptor()
        
        instance = TestClass()
        instance.priority = None
        
        assert instance.priority == 'MEDIUM'
