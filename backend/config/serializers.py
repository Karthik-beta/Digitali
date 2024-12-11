from rest_framework import serializers
from config import models


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['name'] = instance.name.title()
    #     return data

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Designation
        fields = '__all__'

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Division
        fields = '__all__'

class SubDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SubDivision
        fields = '__all__'

class ShopfloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Shopfloor
        fields = '__all__'

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Shift
        fields = '__all__'

class AutoShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AutoShift
        fields = '__all__'