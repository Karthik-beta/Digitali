import { Component, OnInit } from '@angular/core';
import { SharedService } from 'src/app/shared.service';
import { MessageService } from 'primeng/api';
import { LazyLoadEvent } from 'primeng/api';
import { MenuItem } from 'primeng/api';

@Component({
  selector: 'app-mandays',
  templateUrl: './mandays.component.html',
  styleUrl: './mandays.component.scss'
})
export class MandaysComponent implements OnInit {

    mandaysAttendanceList: any[] = [];
    totalRecords: number = 0;
    rowsPerPageOptions: number[] = [10, 20, 30];
    rows: number = 10;
    currentPage: number = 1;
    loading: boolean = false;
    showElements: string = 'true';
    visible: boolean = false;
    position: string = 'top';
    date: string = '';
    logdate: string = '';
    items: MenuItem[] = [];

    constructor(private service: SharedService, private messageService: MessageService,) { }

    ngOnInit(): void {

        this.items = [
            // { label: 'Import', icon: 'fas fa-file-import' },
            { label: 'Export Mandays Movements', icon: 'fas fa-download', command: () => this.downloadMandaysAttendanceReport() },
            { label: 'Export Mandays Worked', icon: 'fas fa-download', command: () => this.downloadMandaysWorkedReport() },
            // { separator: true },
        ];
    }

    onDateChange(event: any) {
        const selectedDate = new Date(event);  // Convert the event to a Date object
        const year = selectedDate.getFullYear();
        const month = ('0' + (selectedDate.getMonth() + 1)).slice(-2);  // Months are zero-indexed
        const day = ('0' + selectedDate.getDate()).slice(-2);  // Ensure two digits for the day
        const formattedDate = `${year}-${month}-${day}`;

        this.date = formattedDate;  // Assign the formatted date to the date property

    }

    downloadMandaysAttendanceReport() {
        this.visible = true;

        const params: any = {
            date: this.date,
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

    downloadMandaysWorkedReport() {
        this.visible = true;

        const params: any = {
            date: this.date,
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

    downloadMandaysMissedPunchReport() {
        this.visible = true;

        const params: any = {
            date: this.date,
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
            logdate: this.date,
        };

        console.log('Params:', params); // Check the params object

        this.service.getMandaysAttendanceList(params).subscribe((data: any) => {
            this.mandaysAttendanceList = data.results;
            this.totalRecords = data.count;
            this.loading = false;
        });
    }


}
