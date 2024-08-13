import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { SharedService } from 'src/app/shared.service';
import { DataService } from 'src/app/service/dataservice/data.service';
import { Table } from 'primeng/table';
import { TableLazyLoadEvent } from 'primeng/table';
import { LazyLoadEvent } from 'primeng/api';
import { MessageService, ConfirmationService, ConfirmEventType } from 'primeng/api';
import { MenuItem } from 'primeng/api';
import { debounceTime, distinctUntilChanged, startWith, switchMap, timeout, catchError } from 'rxjs/operators';
import { Observable, Subscription, interval, timer } from 'rxjs';
import { of } from 'rxjs';

@Component({
  selector: 'app-employee-master',
  standalone: false,
//   imports: [],
  templateUrl: './employee-master.component.html',
  styleUrl: './employee-master.component.scss'
})
export class EmployeeMasterComponent implements OnInit, OnDestroy {

    @ViewChild('dt') dt: Table;

    totalRecords: number = 0;
    rowsPerPageOptions: number[] = [10, 20, 30, 50];
    rows: number = this.rowsPerPageOptions[0];
    currentPage: number = 1;
    loading: boolean = true;
    searchQuery: string = '';
    employees: any[] = [];


    text: string = '';
    results: any[] = [];

    items: MenuItem[] = [];

    constructor(
        private service: SharedService,
        private messageService: MessageService,
        private confirmationService: ConfirmationService,
        private dataService: DataService,
        private router: Router
    )
    {

    }




    ngOnInit(): void {

        this.items = [
            { label: 'Import', icon: 'fas fa-file-import' },
            { label: 'Export', icon: 'fas fa-download' },
        ];

        // Load employees data from session storage if available
        const sessionEmployees = sessionStorage.getItem('employees');
        if (sessionEmployees) {
        this.employees = JSON.parse(sessionEmployees);
        }
    }




    private EmployeesListSubscription: Subscription;

    getEmployeesList(event: LazyLoadEvent): void {
        this.loading = true;

        const params: any = {
            page: ((event.first || 0 ) / (event.rows || 5) + 1).toString(),
            page_size: (event.rows || 10).toString(),
            sortField: event.sortField || '',
            ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '',
            search: this.searchQuery || '',
        };

        // Use startWith to trigger an initial HTTP request
        this.EmployeesListSubscription = interval(100000).pipe(
            startWith(0), // emit 0 immediately
            // Use switchMap to switch to a new observable (HTTP request) each time the interval emits
            switchMap(() => this.service.getEmployeeList(params).pipe(
                timeout(10000), // Set timeout to 10 seconds
                catchError(error => {
                    console.error('Request timed out or failed', error);
                    this.loading = false;
                    return of({ results: [], count: 0 }); // Return an empty result set in case of error
                })
            )),
            // Use distinctUntilChanged to filter out repeated values
            distinctUntilChanged((prev, curr) => JSON.stringify(prev) === JSON.stringify(curr))
        ).subscribe((data: any) => {
            this.employees = data.results;
            this.totalRecords = data.count;
            this.loading = false;

            // Store employees data in session storage
            // sessionStorage.setItem('employees', JSON.stringify(this.employees));
        });
    }

    onSearchChange(query: string): void {
        this.searchQuery = query;
        this.dt.filterGlobal(query, 'contains');
    }

    clear(table: Table) {
        table.clear();
    }



    ngOnDestroy() {
        if (this.EmployeesListSubscription) {
            this.EmployeesListSubscription.unsubscribe();
        }
    }

}
