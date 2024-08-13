import { Component, OnInit, ViewChild } from '@angular/core';
import { Table } from 'primeng/table';
import { SharedService } from 'src/app/shared.service';
import { MessageService } from 'primeng/api';
import { LazyLoadEvent } from 'primeng/api';
import { debounceTime, distinctUntilChanged, startWith, switchMap, timeout, catchError } from 'rxjs/operators';
import { Observable, Subscription, interval, timer } from 'rxjs';
import { of } from 'rxjs';

@Component({
  selector: 'app-monthly-in-out',
  templateUrl: './monthly-in-out.component.html',
  styleUrl: './monthly-in-out.component.scss'
})
export class MonthlyInOutComponent implements OnInit {

    @ViewChild('dt') dt: Table;

    reportList: any;

    metrics: any;

    date: Date;

    rangeDates: Date[];

    metricsDate = [];

    metricsPresent = [];

    metricsAbsent = [];

    metricsLateEntry = [];

    metricsEarlyExit = [];

    metricsOvertime = [];

    data: any;

    options: any;

    totalRecords: number = 0;

    rowsPerPageOptions: number[] = [10, 20, 30];

    rows: number = 10;

    currentPage: number = 1;

    loading: boolean = false;

    searchQuery: string = '';

    company_name: string = '';

    location_name: string = '';

    companies: any[] = [];

    locations: any[] = [];

    selectedCompany: any;

    selectedLocation: any;

    showElements: string = 'true';

    constructor(
        private service: SharedService,
        private messageService: MessageService,
    ) { }

    ngOnInit() {
        this.initCharts();
        this.getAttendanceMonthlyMetrics();
        this.getCompaniesList();
        this.getLocationsList();
    }

    initCharts() {
        const documentStyle = getComputedStyle(document.documentElement);
        const textColor = documentStyle.getPropertyValue('--text-color');
        const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary');
        const surfaceBorder = documentStyle.getPropertyValue('--surface-border');

        this.data = {
            labels: this.metricsDate,
            datasets: [
                {
                    label: 'Present',
                    backgroundColor: documentStyle.getPropertyValue('--green-500'),
                    borderColor: documentStyle.getPropertyValue('--green-500'),
                    data: this.metricsPresent
                },
                {
                    label: 'Absent',
                    backgroundColor: documentStyle.getPropertyValue('--red-500'),
                    borderColor: documentStyle.getPropertyValue('--red-500'),
                    data: this.metricsAbsent
                },
                {
                    label: 'Late Entry',
                    backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                    borderColor: documentStyle.getPropertyValue('--indigo-400'),
                    data: this.metricsLateEntry
                },
                {
                    label: 'Early Exit',
                    backgroundColor: documentStyle.getPropertyValue('--teal-400'),
                    borderColor: documentStyle.getPropertyValue('--teal-400'),
                    data: this.metricsEarlyExit
                },
                {
                    label: 'Overtime',
                    backgroundColor: documentStyle.getPropertyValue('--purple-400'),
                    borderColor: documentStyle.getPropertyValue('--purple-400'),
                    data: this.metricsOvertime
                }
            ]
        };

        this.options = {
            maintainAspectRatio: false,
            aspectRatio: 1.5,
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary,
                        font: {
                            weight: 500
                        }
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                }

            }
        };
    }

    getAttendanceReport(event: LazyLoadEvent) {
        this.loading = true;

        const params: any = {
            page: ((event.first || 0 ) / (event.rows || 5) + 1).toString(),
            page_size: (event.rows || 10).toString(),
            sortField: event.sortField || '',
            ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '',
            search: this.searchQuery || '',
            logdate: this.date || '',
            company_name: this.company_name || '',
            location_name: this.location_name || '',
        };

        if (this.rangeDates && this.rangeDates.length === 2 && this.rangeDates[0] && this.rangeDates[1]) {
            params.date_from = this.formatDate(this.rangeDates[0]);
            params.date_to = this.formatDate(this.rangeDates[1]);
        }

        // this.service.getAttendanceList(params).subscribe((data: any) => {
        //     this.reportList = data.results;
        //     this.totalRecords = data.count;
        //     this.loading = false;
        // });
        this.service.getAttendanceList(params).pipe(
            timeout(10000), // Set timeout to 10 seconds
            catchError(error => {
                console.error('Request timed out or failed', error);
                this.loading = false;
                return of({ results: [], count: 0 }); // Return an empty result set in case of error
            })
        ).subscribe((data: any) => {
            this.reportList = data.results;
            this.totalRecords = data.count;
            this.loading = false;
        });
    }

    onSearchChange(query: string): void {
        this.searchQuery = query;
        this.dt.filterGlobal(query, 'contains');
    }

    onDateChange(query: Date): void {
        const formattedDate = this.formatDate(query);
        this.searchQuery = formattedDate;
        this.dt.filterGlobal(formattedDate, 'contains');
        console.log(formattedDate);
    }

    onDateRangeChange(event: any) {
        if (this.rangeDates && this.rangeDates.length === 2 && this.rangeDates[0] && this.rangeDates[1]) {
            const params: any = {
                page: ((event.first || 0 ) / (event.rows || 5) + 1).toString(),
                page_size: (event.rows || 10).toString(),
                sortField: event.sortField || '',
                ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '',
                date_from: this.formatDate(this.rangeDates[0]),
                date_to: this.formatDate(this.rangeDates[1]),
            };
          this.getAttendanceReport(params);
        }
    }

    // formatDate(date: Date): string {
    //     const year = date.getFullYear();
    //     const month = ('0' + (date.getMonth() + 1)).slice(-2); // Adding 1 to month as it's 0-indexed
    //     const day = ('0' + date.getDate()).slice(-2);
    //     return `${year}-${month}-${day}`;
    // }

    formatDate(date: Date): string {
        if (!date) {
          return '';
        }
        const year = date.getFullYear().toString(); // Keeping the full year
        const month = ('0' + (date.getMonth() + 1)).slice(-2); // Adding 1 to month as it's 0-indexed
        const day = ('0' + date.getDate()).slice(-2);
        return `${month}-${day}-${year}`; // Format mm-dd-yyyy
      }

    clear(table: Table) {
        table.clear();
        this.searchQuery = '';

        this.getAttendanceReport(
            {
                first: 0, rows: this.rows, sortField: '', sortOrder: 1
            }
        );

        this.dt.reset();
        this.showElements = 'true';
        this.company_name = '';
        this.location_name = '';
    }

    private AttendanceMonthlyMetricSubscription: Subscription;

    getAttendanceMonthlyMetrics() {
        this.AttendanceMonthlyMetricSubscription = interval(10000).pipe(
            startWith(0), // emit 0 immediately
            // Use switchMap to switch to a new observable (HTTP request) each time the interval emits
            switchMap(() => this.service.getAttendanceMonthlyMetrics()),
            // Use distinctUntilChanged to filter out repeated values
            distinctUntilChanged((prev, curr) => JSON.stringify(prev) === JSON.stringify(curr))
        ).subscribe((data: any) => {
            // this.metrics = data.daily_metrics;
            this.metricsDate = data.daily_metrics.map((item: any) => item.date);
            this.metricsPresent = data.daily_metrics.map((item: any) => item.present);
            this.metricsAbsent = data.daily_metrics.map((item: any) => item.absent);
            this.metricsLateEntry = data.daily_metrics.map((item: any) => item.late_entry);
            this.metricsEarlyExit = data.daily_metrics.map((item: any) => item.early_exit);
            this.metricsOvertime = data.daily_metrics.map((item: any) => item.overtime);

            this.initCharts();
        });
    }

    getCompaniesList() {

        const params: any = {
            page: 1,
            page_size: 100,
            sortField: '',
            ordering: '',
        };

        this.service.getCompanies(params).subscribe((data: any) => {
            this.companies = data.results;
        });
    }

    getLocationsList() {

        const params: any = {
            page: 1,
            page_size: 100,
            sortField: '',
            ordering: '',
        };

        this.service.getLocations(params).subscribe((data: any) => {
            this.locations = data.results;
        });
    }

    assignCompanyId(selectedCompany: any) {
        // Set the search query to the selected company ID
        this.company_name = selectedCompany.name;
        this.getAttendanceReport({ first: 0, rows: this.rows, sortField: '', sortOrder: 1 });
    }

    assignLocationId(selectedLocation: any) {
        // Set the search query to the selected company ID
        this.location_name = selectedLocation.name;
        this.getAttendanceReport({ first: 0, rows: this.rows, sortField: '', sortOrder: 1 });
    }

    ngOnDestroy() {

        if (this.AttendanceMonthlyMetricSubscription) {
            this.AttendanceMonthlyMetricSubscription.unsubscribe();
        }
    }

}
