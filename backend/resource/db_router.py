# class LogsRouter:
#     def db_for_read(self, model, **hints):
#         if model._meta.model_name == 'logs':
#             return 'Attendance_DB'
#         return 'default'  # Fallback to default database for other models

#     def db_for_write(self, model, **hints):
#         # Avoid writing to the legacy database
#         if model._meta.model_name == 'logs':
#             return None
#         return 'default'  # Write to default database

#     def allow_relation(self, obj1, obj2, **hints):
#         # Allow relations only if both objects are in the same database
#         if obj1._state.db == 'Attendance_DB' and obj2._state.db == 'Attendance_DB':
#             return True
#         return None

#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         # Prevent migration of the 'logs' model
#         if model_name == 'logs':
#             return db == 'Attendance_DB'
#         return db == 'default'
