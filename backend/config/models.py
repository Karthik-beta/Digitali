from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Company, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'company'

class Location(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Location, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'location'

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Department, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'department'

class Designation(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Designation, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'designation'

class Division(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Division, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'division'

class SubDivision(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(SubDivision, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'subdivision'

class Shopfloor(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super(Shopfloor, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'shopfloor'

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_at_start_time = models.DurationField() 
    grace_period_at_end_time = models.DurationField()
    half_day_threshold = models.DurationField()
    full_day_threshold = models.DurationField()    
    overtime_threshold_before_start = models.DurationField()  
    overtime_threshold_after_end = models.DurationField()
    lunch_in = models.TimeField(blank=True, null=True)
    lunch_out = models.TimeField(blank=True, null=True)
    lunch_duration = models.DurationField(blank=True, null=True)
    night_shift = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_night_shift(self):
        if self.start_time > self.end_time:
            return True
        return False

    def __str__(self):
        return self.name
    
    def calculate_lunch_duration(self):
        return self.lunch_out - self.lunch_in
    
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super(Shift, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'shift'

class AutoShift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    tolerance_start_time = models.DurationField()
    tolerance_end_time = models.DurationField()
    # grace_period_at_start_time = models.DurationField()
    # grace_period_at_end_time = models.DurationField()
    half_day_threshold = models.DurationField()
    full_day_threshold = models.DurationField()    
    overtime_threshold_before_start = models.DurationField()  
    overtime_threshold_after_end = models.DurationField() 
    lunch_in = models.TimeField()
    lunch_out = models.TimeField()
    lunch_duration = models.DurationField()
    night_shift = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_night_shift(self):
        if self.start_time > self.end_time:
            return True
        return False

    def calculate_lunch_duration(self):
        return self.lunch_out - self.lunch_in

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super(AutoShift, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'auto_shift'