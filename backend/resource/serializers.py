from rest_framework import serializers
from resource.models import (Employee, Attendance, Logs)

# from config import models as config
# from config.models import config

class EmployeeSerializer(serializers.ModelSerializer):
    company_name = serializers.PrimaryKeyRelatedField(read_only=True, source='company.name')
    location_name = serializers.PrimaryKeyRelatedField(read_only=True, source='location.name')
    department_name = serializers.PrimaryKeyRelatedField(read_only=True, source='department.name')
    designation_name = serializers.PrimaryKeyRelatedField(read_only=True, source='designation.name')
    division_name = serializers.PrimaryKeyRelatedField(read_only=True, source='division.name')
    subdivision_name = serializers.PrimaryKeyRelatedField(read_only=True, source='subdivision.name')
    shopfloor_name = serializers.PrimaryKeyRelatedField(read_only=True, source='shopfloor.name')
    
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeDropdownSerializer(serializers.ModelSerializer):
    combined_field = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['employee_id', 'combined_field']
    
    def get_combined_field(self, obj):
        return f"{obj.employee_name}  [ {obj.employee_id} ]" 


class AttendanceSerializer(serializers.ModelSerializer):
    employee_id_id = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.employee_id')
    profile_pic = serializers.ImageField(read_only=True, source='employeeid.profile_pic') 
    employee_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.employee_name')
    device_enroll_id = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.device_enroll_id')
    company_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.company.name')
    location_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.location.name')
    job_type = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.job_type')
    department_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.department.name')
    category = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.category')
    designation_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.designation.name')
    shift_name = serializers.PrimaryKeyRelatedField(read_only=True, source='employeeid.shift.name')

    class Meta:
        model = Attendance
        fields = '__all__'


class LogsSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Logs
        fields = '__all__'

    def get_employee_name(self, obj):
        try:
            employee = Employee.objects.get(employee_id=obj.employeeid)
            return employee.employee_name
        except Employee.DoesNotExist:
            return None