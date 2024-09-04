class LogsRouter:
    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'logs':
            return 'Attendance_DB'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'logs':
            return 'Attendance_DB'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'logs':
            return db == 'Attendance_DB'
        return None
