"""
Tests unitaires pour les décorateurs de classes
"""
import pytest
import time
from datetime import datetime
from core.decorators import (
    add_performance_tracking,
    auto_configuration_validation,
    register_in_global_registry,
    add_circuit_breaker
)
from core.metaclasses import NotificationRegistry


class TestPerformanceTrackingDecorator:
    """Tests pour @add_performance_tracking"""
    
    def test_adds_performance_metrics_attribute(self):
        """Vérifie que le décorateur ajoute _performance_metrics"""
        
        @add_performance_tracking
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        assert hasattr(instance, '_performance_metrics')
        assert isinstance(instance._performance_metrics, list)
    
    def test_adds_tracking_methods(self):
        """Vérifie que les méthodes de tracking sont ajoutées"""
        
        @add_performance_tracking
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        assert hasattr(instance, '_track_performance')
        assert hasattr(instance, 'get_performance_metrics')
        assert hasattr(instance, 'get_average_performance')
        assert hasattr(instance, 'clear_performance_metrics')
    
    def test_track_performance_records_metric(self):
        """Vérifie l'enregistrement des métriques"""
        
        @add_performance_tracking
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        instance._track_performance(0.123, 'test_method')
        
        metrics = instance.get_performance_metrics()
        assert len(metrics) == 1
        assert metrics[0]['method'] == 'test_method'
        assert metrics[0]['duration'] == 0.123
        assert isinstance(metrics[0]['timestamp'], datetime)
    
    def test_get_average_performance(self):
        """Vérifie le calcul de la performance moyenne"""
        
        @add_performance_tracking
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        instance._track_performance(0.1, 'method1')
        instance._track_performance(0.2, 'method2')
        instance._track_performance(0.3, 'method3')
        
        avg = instance.get_average_performance()
        assert avg == 0.2
    
    def test_clear_performance_metrics(self):
        """Vérifie la réinitialisation des métriques"""
        
        @add_performance_tracking
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        instance._track_performance(0.1, 'method1')
        instance._track_performance(0.2, 'method2')
        
        assert len(instance.get_performance_metrics()) == 2
        
        instance.clear_performance_metrics()
        
        assert len(instance.get_performance_metrics()) == 0


class TestAutoConfigurationValidationDecorator:
    """Tests pour @auto_configuration_validation"""
    
    def test_calls_validate_configuration_on_init(self):
        """Vérifie que validate_configuration est appelée à l'initialisation"""
        
        @auto_configuration_validation
        class TestClass:
            def __init__(self):
                self._notification_type = 'test'
        
        instance = TestClass()
    
    def test_raises_if_notification_type_missing(self):
        """Vérifie l'exception si _notification_type manquant"""
        
        @auto_configuration_validation
        class TestClass:
            def __init__(self):
                pass
        
        with pytest.raises(ValueError) as exc_info:
            TestClass()
        
        assert "Type de notification non défini" in str(exc_info.value)
    
    def test_uses_custom_validate_configuration(self):
        """Vérifie l'utilisation d'une validation personnalisée"""
        
        @auto_configuration_validation
        class TestClass:
            def __init__(self):
                self.validated = False
            
            def validate_configuration(self):
                self.validated = True
        
        instance = TestClass()
        assert instance.validated is True


class TestRegisterInGlobalRegistryDecorator:
    """Tests pour @register_in_global_registry"""
    
    def setup_method(self):
        """Nettoie le registre avant chaque test"""
        NotificationRegistry._registry.clear()
    
    def test_registers_class_in_registry(self):
        """Vérifie l'enregistrement dans le registre"""
        
        @register_in_global_registry
        class TestNotifier:
            pass
        
        registered = NotificationRegistry.get('TestNotifier')
        assert registered == TestNotifier
    
    def test_returns_original_class(self):
        """Vérifie que le décorateur retourne la classe originale"""
        
        @register_in_global_registry
        class TestNotifier:
            pass
        
        assert TestNotifier.__name__ == 'TestNotifier'


class TestCircuitBreakerDecorator:
    """Tests pour @add_circuit_breaker"""
    
    def test_adds_circuit_breaker_attributes(self):
        """Vérifie que les attributs circuit breaker sont ajoutés"""
        
        @add_circuit_breaker(max_failures=3, timeout=60)
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        assert hasattr(instance, '_circuit_breaker_failures')
        assert hasattr(instance, '_circuit_breaker_last_failure')
        assert hasattr(instance, '_circuit_breaker_max_failures')
        assert hasattr(instance, '_circuit_breaker_timeout')
        
        assert instance._circuit_breaker_max_failures == 3
        assert instance._circuit_breaker_timeout == 60
    
    def test_adds_circuit_breaker_methods(self):
        """Vérifie que les méthodes circuit breaker sont ajoutées"""
        
        @add_circuit_breaker(max_failures=3, timeout=60)
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        assert hasattr(instance, 'is_circuit_open')
        assert hasattr(instance, 'record_failure')
        assert hasattr(instance, 'record_success')
    
    def test_circuit_opens_after_max_failures(self):
        """Vérifie que le circuit s'ouvre après max_failures"""
        
        @add_circuit_breaker(max_failures=3, timeout=60)
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        assert not instance.is_circuit_open()
        
        instance.record_failure()
        instance.record_failure()
        instance.record_failure()
        
        assert instance.is_circuit_open()
    
    def test_circuit_closes_after_timeout(self):
        """Vérifie que le circuit se ferme après le timeout"""
        
        @add_circuit_breaker(max_failures=2, timeout=1)
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        instance.record_failure()
        instance.record_failure()
        
        assert instance.is_circuit_open()
        
        time.sleep(1.1)
        
        assert not instance.is_circuit_open()
    
    def test_record_success_resets_failures(self):
        """Vérifie que record_success réinitialise les échecs"""
        
        @add_circuit_breaker(max_failures=3, timeout=60)
        class TestClass:
            def __init__(self):
                pass
        
        instance = TestClass()
        
        instance.record_failure()
        instance.record_failure()
        
        assert instance._circuit_breaker_failures == 2
        
        instance.record_success()
        
        assert instance._circuit_breaker_failures == 0
        assert instance._circuit_breaker_last_failure is None


class TestDecoratorCombinations:
    """Tests pour les combinaisons de décorateurs"""
    
    def test_multiple_decorators_work_together(self):
        """Vérifie que plusieurs décorateurs fonctionnent ensemble"""
        
        @add_performance_tracking
        @add_circuit_breaker(max_failures=3, timeout=60)
        class TestClass:
            def __init__(self):
                self._notification_type = 'test'
        
        instance = TestClass()
        
        assert hasattr(instance, '_performance_metrics')
        assert hasattr(instance, 'is_circuit_open')
        assert hasattr(instance, 'get_performance_metrics')
