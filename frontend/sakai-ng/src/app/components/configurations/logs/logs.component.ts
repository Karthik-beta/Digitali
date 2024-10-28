import { Component, OnInit, ViewChild } from '@angular/core';
import { Table } from 'primeng/table';
import { SharedService } from 'src/app/shared.service';
import { LazyLoadEvent } from 'primeng/api';

@Component({
  selector: 'app-logs',
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss'
})
export class LogsComponent implements OnInit {

    @ViewChild('dt') dt: Table;

    logList: any

    constructor(private service: SharedService) {}

    ngOnInit() {

    }

    totalRecords: number = 0;
    rowsPerPageOptions: number[] = [10, 20, 30];
    rows: number = 10;
    currentPage: number = 1;
    loading: boolean = false;
    searchQuery: string = '';

    onSearchChange(query: string): void {
        this.searchQuery = query;
        this.dt.filterGlobal(query, 'exact');
    }

    getLogReport(event: LazyLoadEvent): void {
        this.loading = true;

        const params: any = {
            page: ((event.first || 0 ) / (event.rows || 5) + 1).toString(),
            page_size: (event.rows || 10).toString(),
            sortField: event.sortField || 'log_datetime',
            ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '-log_datetime'
        };

        // Include employeeid in the params if it exists
        if (this.searchQuery) {
            params.employeeid = this.searchQuery;  // Set employeeid directly
        }

        this.service.getLogReport(params).subscribe((data: any) => {
            this.logList = data.results;
            this.totalRecords = data.count;
            this.loading = false;
        });

        console.log('getLogReport', params);

    }


}
