from django.urls import re_path
from resource.views import (
                            EmployeeListCreate, EmployeeRetrieveUpdateDestroy, EmployeeIdGet, 
                            AttendanceListCreate, ExportAttendanceExcelView, AttendanceMetricsAPIView,
                            AttendanceMonthlyMetricsAPIView, LogsListCreate, LogsRetrieveUpdateDestroy,
                            EmployeeDropdownList, ExportEmployeeAttendanceExcelView, ExportAllEmployeeAttendanceExcelView, 
                            LastLogIdView, MandaysAttendanceListCreate, ManDaysAttendanceExcelExport, ManDaysWorkedExcelExport,
                            ManDaysMissedPunchExcelExport )

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    re_path(r'^unique_id/$', EmployeeIdGet.as_view(), name='employee-options-list'),
    
    re_path(r'^employee/$', EmployeeListCreate.as_view(), name='employee-list-create'),
    re_path(r'^employee/(?P<id>\d+)/$', EmployeeRetrieveUpdateDestroy.as_view(), name='employee-retrieve-update-destroy'),

    re_path(r'^attendance/$', AttendanceListCreate.as_view(), name='attendance-list-create'),

    re_path(r'^attendance/export/$', ExportAttendanceExcelView.as_view(), name='attendance-export'),

    re_path(r'^attendance/metrics/daily/$', AttendanceMetricsAPIView.as_view(), name='attendance-metrics-daily'),

    re_path(r'^attendance/metrics/monthly/$', AttendanceMonthlyMetricsAPIView.as_view(), name='attendance-metrics-monthly'),

    re_path(r'^logs/$', LogsListCreate.as_view(), name='logs-list-create'),
    re_path(r'^logs/(?P<id>\d+)/$', LogsRetrieveUpdateDestroy.as_view(), name='logs-list-create'),

    re_path(r'^employee/dropdown/$', EmployeeDropdownList.as_view(), name='employee-dropdown-list'),

    re_path(r'^attendance/employee/$', ExportEmployeeAttendanceExcelView.as_view()),

    re_path(r'^attendance/export/allemployees/$', ExportAllEmployeeAttendanceExcelView.as_view(), name='attendance-export'),

    re_path(r'^last_log_id/$', LastLogIdView.as_view(), name='attendance-export'),

    re_path(r'^attendance/mandays/$', MandaysAttendanceListCreate.as_view(), name='logs-list-create'),

    re_path(r'^attendance/mandays/report/$', ManDaysAttendanceExcelExport.as_view(), name='logs-list-create'),

    re_path(r'^attendance/mandays/work_report/$', ManDaysWorkedExcelExport.as_view(), name='logs-list-create'),

    re_path(r'^attendance/mandays/missed_punch_report/$', ManDaysMissedPunchExcelExport.as_view(), name='logs-list-create'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
