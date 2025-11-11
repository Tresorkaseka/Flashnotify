# Système de Notification Académique

## Overview

An academic notification system built with Flask that demonstrates advanced Python OOP concepts including class decorators, descriptors, and metaclasses. The system sends notifications through multiple channels (Email, SMS, Push) based on emergency types and user preferences, with automatic priority assignment, performance tracking, and circuit breaker patterns.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask 3.0.0** - Lightweight web framework chosen for its simplicity and flexibility in demonstrating OOP patterns without framework overhead
- **Template Engine**: Jinja2 (Flask default) for server-side rendering with Bootstrap 5 UI
- **Session Management**: Flask sessions with configurable secret key

### Database Layer
- **ORM**: Flask-SQLAlchemy 3.1.1 for database abstraction
- **Default**: SQLite for development (file-based: `notifications.db`)
- **Production Ready**: PostgreSQL support via psycopg2-binary 2.9.9
- **Database URL**: Configurable via `DATABASE_URL` environment variable

**Data Models**:
- `User`: Stores user information with validated email/phone via descriptors
- `Notification`: Records sent notifications with emergency type, priority, and delivery status
- `PerformanceMetric`: Tracks notification sending performance metrics

**Validation Strategy**: Dual validation approach:
- Descriptors (`EmailDescriptor`, `PhoneDescriptor`) for class-level attribute validation
- Helper functions (`validate_email`, `validate_phone`, `validate_priority`) for model-level validation
- Both share the same validation logic (regex patterns)

### Core Architecture - Advanced OOP Patterns

The system architecture is built around three advanced Python OOP concepts:

#### 1. Class Decorators (`core/decorators.py`)
Provide cross-cutting functionality without modifying existing code:

- `@add_performance_tracking`: Automatically tracks method execution time, maintains metrics history, calculates averages
- `@auto_configuration_validation`: Validates required configuration fields at instantiation
- `@register_in_global_registry`: Auto-registers notification classes for discovery
- `@add_circuit_breaker`: Implements resilience pattern to handle failures gracefully with automatic recovery

**Design Decision**: Decorators chosen over inheritance to allow composable, stackable functionality that can be mixed and matched per class needs.

#### 2. Descriptors (`core/descriptors.py`)
Control attribute access with automatic validation:

- `EmailDescriptor`: Validates email format using regex pattern
- `PhoneDescriptor`: Validates international phone numbers (E.164 format)
- Instance-based storage using `id(instance)` as key to avoid conflicts

**Design Decision**: Descriptors provide reusable validation logic that works at the attribute level, ensuring data integrity before it reaches the database layer.

#### 3. Metaclasses (`core/metaclasses.py`)
Automate class creation and registration:

- `NotificationMeta`: Auto-generates validators from `required_fields`, adds descriptions, sets notification types
- `NotificationRegistry`: Global registry for all notification channel classes
- `ChannelMeta`: (Referenced but implementation not shown in provided files)

**Design Decision**: Metaclasses reduce boilerplate by generating repetitive code patterns automatically during class definition, ensuring consistency across notification types.

### Notification System (`core/notification_system.py`)

**Emergency Types** (Enum):
- Weather, Security, Health, Infrastructure, Academic
- Each type auto-maps to a priority level

**Priority System** (Enum):
- CRITICAL (4): Security, Health emergencies
- HIGH (3): Weather alerts  
- MEDIUM (2): Infrastructure issues
- LOW (1): Academic announcements

**Channel Selection Logic**:
- User preference-based routing (email vs push)
- Emergency type determines if multi-channel broadcast is needed
- Critical/High priority notifications may trigger multiple channels

### Application Routes

**Main Routes**:
- `/` - Send notification form (index)
- `/send-notification` [POST] - Process and send notification
- `/dashboard` - View notification statistics and history
- `/admin` - User management (CRUD operations)

**Data Flow**:
1. User selects recipient and emergency type
2. Priority automatically determined via `get_priority(emergency_type)`
3. Notification routed through decorated `AcademicNotifier`
4. Performance metrics tracked automatically
5. Results stored in database
6. User receives feedback via flash messages

### Configuration Management

**Environment Variables**:
- `SESSION_SECRET`: Flask session secret (defaults to dev key)
- `DATABASE_URL`: Database connection string (defaults to SQLite)

**Security Considerations**: 
- Secret key should be changed in production
- Database credentials externalized via environment variables
- Email/phone validation prevents injection attacks

### Frontend Architecture

- **Bootstrap 5**: Responsive UI framework
- **Server-Side Rendering**: Jinja2 templates extend `base.html`
- **Component Structure**: 
  - `base.html`: Navigation, flash messages, footer
  - `index.html`: Notification sending form
  - `dashboard.html`: Statistics and notification history
  - `admin.html`: User management interface
- **Custom CSS**: `static/css/style.css` for additional styling

### Performance & Resilience

**Performance Tracking**:
- Automatic timing of notification sends via `@add_performance_tracking`
- Metrics stored in memory and database (`PerformanceMetric` model)
- Dashboard displays average performance statistics

**Resilience Patterns**:
- Circuit Breaker via `@add_circuit_breaker` prevents cascading failures
- Configurable failure threshold and timeout periods
- Automatic circuit reset after recovery period

**Logging**:
- `@log_notification` function decorator for method-level logging
- Console-based logging for development

## External Dependencies

### Database
- **PostgreSQL**: Primary production database (via `psycopg2-binary`)
- **SQLite**: Development/fallback database (no additional dependencies)
- **Connection**: Managed via Flask-SQLAlchemy ORM

### Python Packages
- `Flask==3.0.0`: Web framework
- `Flask-SQLAlchemy==3.1.1`: ORM layer
- `psycopg2-binary==2.9.9`: PostgreSQL adapter
- `python-dotenv==1.0.0`: Environment variable management

### Frontend Libraries (CDN)
- **Bootstrap 5.3.0**: UI framework (loaded via CDN in `base.html`)
- No JavaScript bundling or build process required

### Third-Party Services
None currently integrated, but the architecture supports:
- Email providers (SMTP configuration would be added to `AcademicNotifier`)
- SMS gateways (Twilio, etc.)
- Push notification services (Firebase, etc.)

**Integration Pattern**: Channel-specific implementations would extend base notification classes and be automatically registered via `@register_in_global_registry` decorator.