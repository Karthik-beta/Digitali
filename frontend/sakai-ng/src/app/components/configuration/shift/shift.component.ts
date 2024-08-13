import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Table } from 'primeng/table';
import { LazyLoadEvent } from 'primeng/api';
import { SharedService } from 'src/app/shared.service';
import { EventemitterService } from 'src/app/service/eventemitter/eventemitter.service';
import { debounceTime, distinctUntilChanged, startWith, switchMap, tap } from 'rxjs/operators';
import { Observable, Subscription, interval, timer } from 'rxjs';
import { MessageService, ConfirmationService, ConfirmEventType } from 'primeng/api';

@Component({
  selector: 'app-shift',
  templateUrl: './shift.component.html',
  styleUrl: './shift.component.scss'
})
export class ShiftComponent implements OnInit, OnDestroy {

    @ViewChild('dt') dt: Table;

    shifts: any[] = [];

    display: boolean = false;
    ModalTitle:string="";
    location: any;

    id: number = 0;
    name: string = '';
    start_time: string = '';
    end_time: string = '';
    grace_period: string = '';
    overtime_threshold: string = '';

    constructor(
        private service:SharedService,
        private messageService: MessageService,
        private confirmationService: ConfirmationService,
        private eventEmitterService: EventemitterService
    ) {}

    ngOnInit() {

    }

    totalRecords: number = 0;
    rowsPerPageOptions: number[] = [5, 10, 20, 30];
    rows: number = this.rowsPerPageOptions[0];
    currentPage: number = 1;
    loading: boolean = true;
    searchQuery: string = '';

    private ShiftListSubscription: Subscription;

    getShiftsList(event: LazyLoadEvent): void {
        this.loading = true;

        const params: any = {
          page: ((event.first || 0) / (event.rows || 5) + 1).toString(),
          page_size: (event.rows || 10).toString(),
          sortField: event.sortField || '',
          ordering: event.sortField ? `${event.sortOrder === 1 ? '' : '-'}${event.sortField}` : '',
          search: this.searchQuery || '',

          // Add any other query parameters here
        };

        this.ShiftListSubscription = this.service.getShifts(params).subscribe({
            next: (response) => {
                this.shifts = response.results;
                this.totalRecords = response.count;
            },
            error: (error) => {
                // Handle error if needed
                console.error('Error fetching Shifts:', error);
            }
        });

        this.loading = false;
    }

    onSearchChange(query: string): void {
        this.searchQuery = query;
        this.dt.filterGlobal(query, 'contains');
    }

    clear(table: Table) {
        table.clear();
    }

    addClick() {

        this.id = 0;
        this.name = '';
        this.start_time = '';
        this.end_time = '';
        this.grace_period = '';
        this.overtime_threshold = '';

        this.display = true;
        this.ModalTitle = "Add New Shift";
    }

    addShift() {
        const shift = {
            name: this.name,
            start_time: this.start_time,
            end_time: this.end_time,
            grace_period: this.grace_period,
            overtime_threshold: this.overtime_threshold
        }

        this.loading = true;

        this.service.addShift(shift).subscribe({
            next: (response) => {
                this.dt.reset();

                this.eventEmitterService.invokeGetUpdatedAtList.emit();
                this.display = false;

                // Show success message
                this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Successfully Added New Shift'
                });
            },
            error: (error) => {
                // Show error message
                this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Failed to Add New Shift' });
            }
        });

        this.loading = false;
    }

    editClick(item: any) {

        this.id = item.id;
        this.name = item.name;
        this.start_time = this.start_time,
        this.end_time = this.end_time,
        this.grace_period = this.grace_period,
        this.overtime_threshold = this.overtime_threshold

        this.display = true;
        this.ModalTitle = "Edit Shift Details";
    }

    updateShift() {

        const shift = {
            id: this.id,
            name: this.name,
            start_time: this.start_time,
            end_time: this.end_time,
            grace_period: this.grace_period,
            overtime_threshold: this.overtime_threshold
        }

        this.loading = true;

        this.service.updateShift(shift).subscribe({
            next: (response) => {
                this.dt.reset();

                this.eventEmitterService.invokeGetUpdatedAtList.emit();
                this.display = false;

                // Show success message
                this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Successfully Updated Shift Details'
                });
            },
            error: (error) => {
                // Show error message
                this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Failed to Update Shift Details' });
            }
        });

        this.loading = false;
    }

    deleteClick(item: { id: any }) {
        // Extract the employee_id from the log object
        const id = item.id;

        // Display the confirmation dialog before proceeding with deletion
        this.confirmationService.confirm({
            message: 'Are you sure that you want to delete this Shift?',
            header: 'Confirmation',
            icon: 'pi pi-exclamation-triangle',
            accept: () => {
                this.loading = true;

                // Call the deleteEmployee method from the service
                this.service.deleteLocation(id).subscribe({
                    next: (response) => {

                        this.dt.reset();
                        this.eventEmitterService.invokeGetUpdatedAtList.emit();

                        // Show success message
                        this.messageService.add({
                          severity: 'success',
                          summary: 'Success',
                          detail: 'Shift has been deleted successfully.'
                        });
                    },
                    error: (error) => {
                        // Handle error if needed
                        console.error('Error deleting Shift:', error);

                        // Show error message
                        this.messageService.add({
                        severity: 'error',
                        summary: 'Error',
                        detail: 'Failed to delete Shift.'
                        });
                    }
                });

                this.loading = false;
            },
            reject: () => {
                // User rejected the confirmation, do nothing or handle as needed
                this.messageService.add({ severity: 'error', summary: 'Rejected', detail: 'You have Cancelled' });
                // console.log('Deletion cancelled by user.');
            }
        });
    }

    ngOnDestroy() {

        // Unsubscribe from the interval observable
        if (this.ShiftListSubscription) {
            this.ShiftListSubscription.unsubscribe();
        }
    }
}
