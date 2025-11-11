"""
Décorateurs de classes pour ajouter des fonctionnalités transversales
"""
import time
import functools
from datetime import datetime


def add_performance_tracking(cls):
    """Décorateur pour le suivi automatique des performances"""
    original_init = cls.__init__
    
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._performance_metrics = []
    
    cls.__init__ = __init__
    
    def track_performance(self, duration, method_name='send_notification'):
        """Enregistre une métrique de performance"""
        metric = {
            'method': method_name,
            'duration': duration,
            'timestamp': datetime.now()
        }
        self._performance_metrics.append(metric)
    
    def get_performance_metrics(self):
        """Retourne les métriques de performance"""
        return self._performance_metrics
    
    def get_average_performance(self):
        """Calcule la performance moyenne"""
        if not self._performance_metrics:
            return 0
        total = sum(m['duration'] for m in self._performance_metrics)
        return total / len(self._performance_metrics)
    
    def clear_performance_metrics(self):
        """Réinitialise les métriques de performance"""
        self._performance_metrics.clear()
    
    cls._track_performance = track_performance
    cls.get_performance_metrics = get_performance_metrics
    cls.get_average_performance = get_average_performance
    cls.clear_performance_metrics = clear_performance_metrics
    
    return cls


def auto_configuration_validation(cls):
    """Décorateur pour la validation automatique de la configuration"""
    original_init = cls.__init__
    
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if hasattr(self, 'validate_configuration'):
            self.validate_configuration()
    
    cls.__init__ = __init__
    
    def validate_configuration(self):
        """Valide la configuration de base"""
        if not hasattr(self, '_notification_type'):
            raise ValueError("Type de notification non défini")
    
    if not hasattr(cls, 'validate_configuration'):
        cls.validate_configuration = validate_configuration
    
    return cls


def register_in_global_registry(cls):
    """Décorateur pour l'enregistrement automatique dans le registre global"""
    from core.metaclasses import NotificationRegistry
    
    class_name = cls.__name__
    NotificationRegistry.register(class_name, cls)
    
    return cls


def add_circuit_breaker(max_failures=3, timeout=60):
    """Décorateur pour la gestion automatique des pannes (Circuit Breaker pattern)"""
    def decorator(cls):
        original_init = cls.__init__
        
        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._circuit_breaker_failures = 0
            self._circuit_breaker_last_failure = None
            self._circuit_breaker_max_failures = max_failures
            self._circuit_breaker_timeout = timeout
        
        cls.__init__ = __init__
        
        def is_circuit_open(self):
            """Vérifie si le circuit est ouvert (trop d'échecs)"""
            if self._circuit_breaker_failures >= self._circuit_breaker_max_failures:
                if self._circuit_breaker_last_failure:
                    elapsed = (datetime.now() - self._circuit_breaker_last_failure).seconds
                    if elapsed < self._circuit_breaker_timeout:
                        return True
                    else:
                        self._circuit_breaker_failures = 0
                        return False
            return False
        
        def record_failure(self):
            """Enregistre un échec"""
            self._circuit_breaker_failures += 1
            self._circuit_breaker_last_failure = datetime.now()
        
        def record_success(self):
            """Réinitialise le compteur d'échecs"""
            self._circuit_breaker_failures = 0
            self._circuit_breaker_last_failure = None
        
        cls.is_circuit_open = is_circuit_open
        cls.record_failure = record_failure
        cls.record_success = record_success
        
        return cls
    return decorator
