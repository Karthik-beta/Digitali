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
        this.dt.filterGlobal(query, 'contains');
    }

    getLogReport(event: LazyLoadEvent): void {
        this.loading = true;

        const params: any = {
            page: ((event.first || 0 ) / (event.rows || 5) + 1).toString(),
            page_size: (event.rows || 10).toString(),
            sortField: event.sortField || 'log_datetime',
            ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '-log_datetime',
            search: this.searchQuery || '',
        };

        this.service.getLogReport(params).subscribe((data: any) => {
            this.logList = data.results;
            this.totalRecords = data.count;
            this.loading = false;
        });

        console.log('getLogReport', params);

    }


}
