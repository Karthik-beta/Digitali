from django.db import models
import datetime
from django.db.transaction import atomic

class Employee(models.Model):

    BANK_ACCOUNT_CHOICES = (
        ('Savings Account', 'Savings Account'),
        ('Current Account', 'Current Account'),
        ('Salary Account', 'Salary Account'),
        ('NRI Account', 'NRI Account'),
        ('Pension Account', 'Pension Account'),
        ('Other Account', 'Other Account'),
    )

    CATEGORY_CHOICES = (
        ('Permanent Employee', 'Permanent Employee'),
        ('Temporary Employee', 'Temporary Employee'),
        ('Contractor Employee', 'Contractor Employee'),
    )

    JOB_TYPE_CHOICES = (
        ('Training', 'Training'),
        ('Confirmed', 'Confirmed'),
        ('Professional', 'Professional'),
    )

    JOB_STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Resigned', 'Resigned'),
        ('Absconded', 'Absconded'),
    )

    MARITAL_STATUS_CHOICES = (
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    )

    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    COURSE_TYPE_CHOICES = (
        ('Under Graduate', 'Under Graduate'),
        ('Post Graduate', 'Post Graduate'),
        ('Diploma', 'Diploma'),
        ('Certificate', 'Certificate'),
        ('Other', 'Other'),
    )

    SHIFT_CHOICES = (
        ('GS', 'General Shift'),
        ('Day Shift', 'Day Shift'),
        ('Night Shift', 'Night Shift'),
        ('Rotational Shift', 'Rotational Shift'),
        ('Split Shift', 'Split Shift'),
        ('Flexi Shift', 'Flexi Shift'),
        ('Other Shift', 'Other Shift'),
    )

    WEEK_DAYS_CHOICES = (
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    )
    
    profile_pic = models.ImageField(default="default_pic.jpg",upload_to='profile_pics/', blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True)
    employee_name = models.CharField(max_length=100)
    device_enroll_id = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_no = models.PositiveBigIntegerField(blank=True, null=True)
    pf_no = models.CharField(max_length=20, blank=True, null=True)
    esi_no = models.CharField(max_length=20, blank=True, null=True)
    insurance_no = models.CharField(max_length=20, blank=True, null=True)
    # ar_no = models.CharField(max_length=20, blank=True, null=True)
    # ap_no = models.CharField(max_length=20, blank=True, null=True)
    # cn_no = models.CharField(max_length=20, blank=True, null=True)


    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    bank_account_no = models.CharField(max_length=20, blank=True, null=True)
    bank_account_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_type = models.CharField(max_length=20, choices=BANK_ACCOUNT_CHOICES, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)

    # Official Details
    company = models.ForeignKey('config.Company', on_delete=models.SET_NULL, blank=True, null=True)
    location = models.ForeignKey('config.Location', on_delete=models.SET_NULL, blank=True, null=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, blank=True, null=True)
    department = models.ForeignKey('config.Department', on_delete=models.SET_NULL, blank=True, null=True)
    designation = models.ForeignKey('config.Designation', on_delete=models.SET_NULL, blank=True, null=True)
    division = models.ForeignKey('config.Division', on_delete=models.SET_NULL, blank=True, null=True)
    subdivision = models.ForeignKey('config.SubDivision', on_delete=models.SET_NULL, blank=True, null=True)
    shopfloor = models.ForeignKey('config.Shopfloor', on_delete=models.SET_NULL, blank=True, null=True)
    job_type = models.CharField(max_length=100, choices= JOB_TYPE_CHOICES, blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_leaving = models.DateField(blank=True, null=True)
    job_status = models.CharField(max_length=100, choices=JOB_STATUS_CHOICES, blank=True, null=True)
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='reports', blank=True, null=True)
    alt_reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='alt_reports',blank=True, null=True)
    reason_for_leaving = models.TextField(blank=True, null=True)
 
    # Personal Details
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_no = models.PositiveBigIntegerField(blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    spouse_name = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    uid_no = models.CharField(max_length=20, blank=True, null=True) #aadhar 
    pan_no = models.CharField(max_length=20, blank=True, null=True)
    voter_id = models.CharField(max_length=20, blank=True, null=True)
    driving_license = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    present_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    # Qualifications
    graduation = models.CharField(max_length=100, blank=True, null=True)
    course_type = models.CharField(max_length=100, choices=COURSE_TYPE_CHOICES, blank=True, null=True)
    course = models.CharField(max_length=100, blank=True, null=True)
    place_of_graduation = models.CharField(max_length=100, blank=True, null=True)
    aggregate = models.FloatField(blank=True, null=True)
    year_of_graduation = models.PositiveIntegerField(blank=True, null=True)

    # Work Configuration
    # Weekly Off and Shifts
    shift = models.ForeignKey('config.Shift', on_delete=models.SET_NULL, blank=True, null=True)
    auto_shift = models.BooleanField(default=False)
    first_weekly_off = models.CharField(max_length=20, choices=WEEK_DAYS_CHOICES, blank=True, null=True)
    second_weekly_off = models.CharField(max_length=20, choices=WEEK_DAYS_CHOICES, blank=True, null=True)
    week_off_effective_date = models.DateField(blank=True, null=True)

    # Late/Early/Overtime/Flexi Time Marking
    flexi_time = models.BooleanField(default=False)
    consider_late_entry = models.BooleanField(default=False)
    consider_early_exit = models.BooleanField(default=False)
    consider_extra_hours_worked = models.BooleanField(default=False)
    consider_late_entry_on_holiday = models.BooleanField(default=False)
    consider_early_exit_on_holiday = models.BooleanField(default=False)
    consider_extra_hours_worked_on_holiday = models.BooleanField(default=False)

    # Punch Out Setting
    search_next_day = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.employee_name
    
    def save(self, *args, **kwargs):
        if self.employee_name is not None:
            self.employee_name = self.employee_name.title()

        if self.device_enroll_id is not None:
            self.device_enroll_id = self.device_enroll_id.upper()

        if self.email is not None:
            self.email = self.email.lower()

        if self.bank_name is not None:
            self.bank_name = self.bank_name.title()

        if self.bank_branch is not None:
            self.bank_branch = self.bank_branch.title()

        if self.emergency_contact_name is not None:
            self.emergency_contact_name = self.emergency_contact_name.title()

        if self.spouse_name is not None:
            self.spouse_name = self.spouse_name.title()

        if self.blood_group is not None:
            self.blood_group = self.blood_group.upper()

        if self.country_name is not None:
            self.country_name = self.country_name.title()

        if self.graduation is not None:
            self.graduation = self.graduation.title()

        if self.course is not None:
            self.course = self.course.title()

        if self.place_of_graduation is not None:
            self.place_of_graduation = self.place_of_graduation.title()

        super(Employee, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.profile_pic.delete()
        super(Employee, self).delete(*args, **kwargs)

    


    class Meta:
        ordering = ['id']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        db_table = 'employee'
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['employee_id', 'employee_name', 'email', 'phone_no', 'pf_no', 'esi_no', 
                                 'insurance_no', 'bank_name', 'bank_branch', 'bank_account_no', 'bank_account_name', 
                                 'bank_account_type', 'ifsc_code', 'category', 'job_type', 'job_status', 
                                 'emergency_contact_name', 'emergency_contact_no', 'marital_status', 'spouse_name', 
                                 'blood_group', 'date_of_birth', 'country_name', 'country_code', 'uid_no', 'pan_no', 
                                 'voter_id', 'driving_license',]),
            # Add more indexes as needed
        ]

class Logs(models.Model):
    id = models.AutoField(primary_key=True)
    employeeid = models.CharField(max_length=50, blank=True, null=True)
    log_datetime = models.DateTimeField(blank=True, null=True)
    direction = models.CharField(max_length=50, blank=True, null=True)
    shortname = models.CharField(max_length=50, blank=True, null=True)
    serialno = models.CharField(max_length=50, blank=True, null=True) 

    class Meta:   
        db_table = 'logs'
        
         
class LastLogId(models.Model):
    last_log_id = models.IntegerField(default=0, editable=True)
    
    class Meta:
        db_table = 'last_log_id'

class LastLogIdMandays(models.Model):
    last_log_id = models.IntegerField(default=0, editable=True)
    
    class Meta:
        db_table = 'last_log_id_mandays'

class Attendance(models.Model):
    employeeid = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True)
    logdate = models.DateField()
    first_logtime = models.TimeField(blank=True, null=True)
    last_logtime = models.TimeField(blank=True, null=True)
    direction = models.CharField(max_length=50, blank=True, null=True)
    shortname = models.CharField(max_length=50, blank=True, null=True)
    total_time = models.DurationField(blank=True, null=True)
    late_entry = models.DurationField(blank=True, null=True, default=None)
    early_exit = models.DurationField(blank=True, null=True, default=None)
    overtime = models.DurationField(blank=True, null=True, default=None)
    shift = models.CharField(max_length=50, blank=True, null=True)
    shift_status = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        unique_together = ('employeeid', 'logdate')
        db_table = 'attendance'
    
    # def save(self, *args, **kwargs):
    #     # Check and replace "00:00:00" with null for specified fields
    #     fields_to_replace = ['late_entry', 'early_exit', 'overtime']
    #     for field_name in fields_to_replace:
    #         field_value = getattr(self, field_name)
    #         if field_value == datetime.time(0, 0):
    #             setattr(self, field_name, None)
        
    #     super(Attendance, self).save(*args, **kwargs)

class ManDaysAttendance(models.Model):
    employeeid = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True)
    shift = models.CharField(max_length=50, blank=True, null=True)
    shift_status = models.CharField(max_length=50, blank=True, null=True)
    logdate = models.DateField()
    duty_in_1 = models.TimeField(blank=True, null=True)
    duty_out_1 = models.TimeField(blank=True, null=True)
    total_time_1 = models.DurationField(blank=True, null=True)
    duty_in_2 = models.TimeField(blank=True, null=True)
    duty_out_2 = models.TimeField(blank=True, null=True)
    total_time_2 = models.DurationField(blank=True, null=True)
    duty_in_3 = models.TimeField(blank=True, null=True)
    duty_out_3 = models.TimeField(blank=True, null=True)
    total_time_3 = models.DurationField(blank=True, null=True)
    duty_in_4 = models.TimeField(blank=True, null=True)
    duty_out_4 = models.TimeField(blank=True, null=True)
    total_time_4 = models.DurationField(blank=True, null=True)
    duty_in_5 = models.TimeField(blank=True, null=True)
    duty_out_5 = models.TimeField(blank=True, null=True)
    total_time_5 = models.DurationField(blank=True, null=True)
    duty_in_6 = models.TimeField(blank=True, null=True)
    duty_out_6 = models.TimeField(blank=True, null=True)
    total_time_6 = models.DurationField(blank=True, null=True)
    duty_in_7 = models.TimeField(blank=True, null=True)
    duty_out_7 = models.TimeField(blank=True, null=True)
    total_time_7 = models.DurationField(blank=True, null=True)
    duty_in_8 = models.TimeField(blank=True, null=True)
    duty_out_8 = models.TimeField(blank=True, null=True)
    total_time_8 = models.DurationField(blank=True, null=True)
    duty_in_9 = models.TimeField(blank=True, null=True)
    duty_out_9 = models.TimeField(blank=True, null=True)
    total_time_9 = models.DurationField(blank=True, null=True)
    duty_in_10 = models.TimeField(blank=True, null=True)
    duty_out_10 = models.TimeField(blank=True, null=True)
    total_time_10 = models.DurationField(blank=True, null=True)
    total_hours_worked = models.DurationField(blank=True, null=True)

    class Meta:
        db_table = 'mandays_attendance'

class ManDaysMissedPunchAttendance(models.Model):
    employeeid = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True)
    shift = models.CharField(max_length=50, blank=True, null=True)
    shift_status = models.CharField(max_length=50, blank=True, null=True)
    logdate = models.DateField()
    duty_in_1 = models.TimeField(blank=True, null=True)
    duty_out_1 = models.TimeField(blank=True, null=True)
    duty_in_2 = models.TimeField(blank=True, null=True)
    duty_out_2 = models.TimeField(blank=True, null=True)
    duty_in_3 = models.TimeField(blank=True, null=True)
    duty_out_3 = models.TimeField(blank=True, null=True)
    duty_in_4 = models.TimeField(blank=True, null=True)
    duty_out_4 = models.TimeField(blank=True, null=True)
    duty_in_5 = models.TimeField(blank=True, null=True)
    duty_out_5 = models.TimeField(blank=True, null=True)
    duty_in_6 = models.TimeField(blank=True, null=True)
    duty_out_6 = models.TimeField(blank=True, null=True)
    duty_in_7 = models.TimeField(blank=True, null=True)
    duty_out_7 = models.TimeField(blank=True, null=True)
    duty_in_8 = models.TimeField(blank=True, null=True)
    duty_out_8 = models.TimeField(blank=True, null=True)
    duty_in_9 = models.TimeField(blank=True, null=True)
    duty_out_9 = models.TimeField(blank=True, null=True)
    duty_in_10 = models.TimeField(blank=True, null=True)
    duty_out_10 = models.TimeField(blank=True, null=True)

    class Meta:
        db_table = 'mandays_missed_punch_attendance'