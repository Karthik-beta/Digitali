import { Component, OnInit, ViewChild } from '@angular/core';
import { SharedService } from 'src/app/shared.service';
import { MessageService } from 'primeng/api';
import { LazyLoadEvent } from 'primeng/api';
import { Table } from 'primeng/table';
import { MenuItem } from 'primeng/api';
import { Calendar } from 'primeng/calendar';

@Component({
  selector: 'app-mandays',
  templateUrl: './mandays.component.html',
  styleUrl: './mandays.component.scss'
})
export class MandaysComponent implements OnInit {

    @ViewChild('dt') dt: Table;
    @ViewChild('calendar') calendar!: Calendar;

    mandaysAttendanceList: any[] = [];
    totalRecords: number = 0;
    rowsPerPageOptions: number[] = [10, 20, 30];
    rows: number = 10;
    currentPage: number = 1;
    loading: boolean = false;
    showElements: string = 'true';
    visible: boolean = false;
    position: string = 'top';
    dateSelected: Date = new Date();
    dateSelectedString: string = '';
    logdate: string = '';
    items: MenuItem[] = [];

    constructor(private service: SharedService, private messageService: MessageService,) { }

    ngOnInit(): void {

        this.items = [
            // { label: 'Import', icon: 'fas fa-file-import' },
            { label: 'Export Mandays Movements', icon: 'fas fa-download', command: () => this.downloadMandaysAttendanceReport() },
            { label: 'Export Mandays Worked', icon: 'fas fa-download', command: () => this.downloadMandaysWorkedReport() },
            { separator: true },
            { label: 'Reprocess Report', icon: 'fas fa-redo-alt', command: () => this.postReprocessLogs() },
        ];
    }

    onDateChange(event: any) {
        if (event) {
            const selectedDate = new Date(event);
            this.dateSelected = selectedDate;
            this.dateSelectedString = this.formatDate(this.dateSelected);
        } else {
            this.dateSelected = null;
            this.dateSelectedString = '';
        }
    }


    formatDate(date: Date): string {
        if (!date) {
          return '';
        }
        const year = date.getFullYear().toString(); // Keeping the full year
        const month = ('0' + (date.getMonth() + 1)).slice(-2); // Adding 1 to month as it's 0-indexed
        const day = ('0' + date.getDate()).slice(-2);
        return `${year}-${month}-${day}`; // Format mm-dd-yyyy
    }

    downloadMandaysAttendanceReport() {
        this.visible = true;

        const params: any = {
            date: this.dateSelectedString,
        };

        this.service.downloadMandaysAttendanceReport(params).subscribe({
            next: (data) => {
                // Show dialog or perform any pre-download actions

                // Create a Blob object from the response data
                const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

                // Create a URL for the Blob
                const url = window.URL.createObjectURL(blob);

                // Create a link element and set up the download
                const a = document.createElement('a');
                a.href = url;

                // Get the current date and format it
                const currentDate = new Date();
                const formattedDate = currentDate.toISOString().split('T')[0];

                // Define the filename
                const filename = `Mandays_Report_${formattedDate}.xlsx`;
                a.download = filename;

                // Append the link to the body, trigger the click, and remove the link
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Set visibility to false and show success message
                this.visible = false;
                this.messageService.add({
                    severity: 'success',
                    summary: 'Report Downloaded',
                    detail: 'Report is ready to download'
                });
            },
            error: (error) => {
                // Handle any error that might occur during the download
                console.error('Error downloading attendance report:', error);

                // Set visibility to false and show error message
                this.visible = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Error downloading the report'
                });
            }
        });
    }

    clear(table: Table) {
        table.clear();
        // this.showElements = 'true';
        if (this.calendar) {
            this.calendar.value = null;
            this.calendar.updateInputfield();
        }
        this.dateSelected = null; // Reset the model value
        this.dateSelectedString = ''; // Clear the formatted string
        this.onDateChange(null);
    }

    downloadMandaysWorkedReport() {
        this.visible = true;

        const params: any = {
            date: this.dateSelectedString,
        };

        this.service.downloadMandaysWorkedReport(params).subscribe({
            next: (data) => {
                // Show dialog or perform any pre-download actions

                // Create a Blob object from the response data
                const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

                // Create a URL for the Blob
                const url = window.URL.createObjectURL(blob);

                // Create a link element and set up the download
                const a = document.createElement('a');
                a.href = url;

                // Get the current date and format it
                const currentDate = new Date();
                const formattedDate = currentDate.toISOString().split('T')[0];

                // Define the filename
                const filename = `Mandays_Report_${formattedDate}.xlsx`;
                a.download = filename;

                // Append the link to the body, trigger the click, and remove the link
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Set visibility to false and show success message
                this.visible = false;
                this.messageService.add({
                    severity: 'success',
                    summary: 'Report Downloaded',
                    detail: 'Report is ready to download'
                });
            },
            error: (error) => {
                // Handle any error that might occur during the download
                console.error('Error downloading attendance report:', error);

                // Set visibility to false and show error message
                this.visible = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Error downloading the report'
                });
            }
        });
    }

    postReprocessLogs() {
        this.service.reProcessLogs().subscribe({
            next: (data) => {
                // Show success message
                this.messageService.add({
                    severity: 'success',
                    summary: 'Success',
                    detail: 'The report is being reprocessed. Please wait for up to 2 minutes to view/download the report.'
                });
            },
            error: (error) => {
                // Show error message
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Failed to reprocess logs'
                });
            }
        });
    }

    downloadMandaysMissedPunchReport() {
        this.visible = true;

        const params: any = {
            date: this.dateSelectedString,
        };

        this.service.downloadMandaysMissedPunchReport(params).subscribe({
            next: (data) => {
                // Show dialog or perform any pre-download actions

                // Create a Blob object from the response data
                const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

                // Create a URL for the Blob
                const url = window.URL.createObjectURL(blob);

                // Create a link element and set up the download
                const a = document.createElement('a');
                a.href = url;

                // Get the current date and format it
                const currentDate = new Date();
                const formattedDate = currentDate.toISOString().split('T')[0];

                // Define the filename
                const filename = `Mandays_Missed_Punch_${formattedDate}.xlsx`;
                a.download = filename;

                // Append the link to the body, trigger the click, and remove the link
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Set visibility to false and show success message
                this.visible = false;
                this.messageService.add({
                    severity: 'success',
                    summary: 'Report Downloaded',
                    detail: 'Report is ready to download'
                });
            },
            error: (error) => {
                // Handle any error that might occur during the download
                console.error('Error downloading attendance report:', error);

                // Set visibility to false and show error message
                this.visible = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Error downloading the report'
                });
            }
        });
    }


    getMandaysAttendanceReport(event: LazyLoadEvent) {
        this.loading = true;

        const params: any = {
            logdate: this.dateSelectedString,
        };

        this.service.getMandaysAttendanceList(params).subscribe((data: any) => {
            this.mandaysAttendanceList = data.results;
            this.totalRecords = data.count;
            this.loading = false;
        });
    }


}
