import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { access } from 'fs';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import { SharedService } from 'src/app/shared.service';

interface EmployeeForm {
  profilePic: File | null;
  employeeId: string;
  deviceEnrollId: string;
  employeeName: string;
  accessCardNo: string | null;
  email: string | null;
  phoneNo: number | null;
  pfNo: string | null;
  esiNo: string | null;
  insuranceNo: string | null;

  // Bank Details
  bankName: string | null;
  bankBranch: string | null;
  bankAccountNo: string | null;
  bankAccountName: string | null;
  bankAccountType: string | null;
  ifscCode: string | null;

  // Official Details
  company: number | null;
  location: number | null;
  category: string | null;
  department: number | null;
  designation: number | null;
  division: number | null;
  subdivision: number | null;
  shopfloor: number | null;
  jobType: string | null;
  dateOfJoining: Date | null;
  dateOfLeaving: Date | null;
  jobStatus: string;
  reportingManager: number | null;
  altReportingManager: number | null;
  reasonForLeaving: string | null;

  // Work Configuration
  shift: number | null;
  autoShift: boolean;
  flexiTime: boolean;
  considerLateEntry: boolean;
  considerEarlyExit: boolean;
  considerExtraHoursWorked: boolean;
  considerLateEntryOnHoliday: boolean;
  considerEarlyExitOnHoliday: boolean;
  considerExtraHoursWorkedOnHoliday: boolean;
  searchNextDay: boolean;

  // Personal Details
  emergencyContactName: string | null;
  emergencyContactNo: number | null;
  maritalStatus: string | null;
  spouseName: string | null;
  bloodGroup: string | null;
  dateOfBirth: Date | null;
  countryName: string | null;
  countryCode: string | null;
  uidNo: string | null;
  panNo: string | null;
  voterId: string | null;
  drivingLicense: string | null;
  gender: string | null;
  presentAddress: string | null;
  permanentAddress: string | null;
}

@Component({
  selector: 'app-add-edit-employee',
  templateUrl: './add-edit-employee.component.html',
  styleUrls: ['./add-edit-employee.component.scss']
})
export class AddEditEmployeeComponent implements OnInit, OnDestroy {
    employeeForm: FormGroup;
    isEditMode = false;
    employeeId: number | null = null;
    activeStepperNumber: number | undefined = 0;
    private destroy$ = new Subject<void>();

    // Dropdown options
    accountTypes: any[] = [];
    categories: any[] = [];
    countries: any[] = [];
    shifts: any[] = [];
    companies: any[] = [];
    locations: any[] = [];
    departments: any[] = [];
    designations: any[] = [];
    divisions: any[] = [];
    subDivisions: any[] = [];
    shopfloors: any[] = [];

    constructor(
        private fb: FormBuilder,
        private employeeService: SharedService,
        private messageService: MessageService,
        private route: ActivatedRoute,
        private router: Router
    ) {
        this.initForm();
    }

    private initForm(): void {
        this.employeeForm = this.fb.group({
            profilePic: [null],
            employeeId: ['', Validators.required],
            deviceEnrollId: [''],
            employeeName: ['', Validators.required],
            accessCardNo: [''],
            email: ['', [Validators.email]],
            phoneNo: [null],
            pfNo: [''],
            esiNo: [''],
            insuranceNo: [''],

            // Bank Details as nested form group
            bankDetails: this.fb.group({
                bankName: [''],
                bankBranch: [''],
                bankAccountNo: [''],
                bankAccountName: [''],
                bankAccountType: [''],
                ifscCode: ['']
            }),

            // Official Details as nested form group
            officialDetails: this.fb.group({
                company: [null],
                location: [null],
                category: [''],
                department: [null],
                designation: [null],
                division: [null],
                subdivision: [null],
                shopfloor: [null],
                jobType: [''],
                dateOfJoining: [null],
                dateOfLeaving: [null],
                jobStatus: ['Active'],
                reportingManager: [null],
                altReportingManager: [null],
                reasonForLeaving: ['']
            }),

            // Work Configuration as nested form group
            workConfig: this.fb.group({
                shift: [null],
                autoShift: [false],
                flexiTime: [false],
                considerLateEntry: [true],
                considerEarlyExit: [true],
                considerExtraHoursWorked: [true],
                considerLateEntryOnHoliday: [true],
                considerEarlyExitOnHoliday: [true],
                considerExtraHoursWorkedOnHoliday: [true],
                searchNextDay: [false]
            }),

            // Personal Details as nested form group
            personalDetails: this.fb.group({
                emergencyContactName: [''],
                emergencyContactNo: [null],
                maritalStatus: [''],
                spouseName: [''],
                bloodGroup: [''],
                dateOfBirth: [null],
                countryName: [''],
                countryCode: [''],
                uidNo: [''],
                panNo: [''],
                voterId: [''],
                drivingLicense: [''],
                gender: [''],
                presentAddress: [''],
                permanentAddress: ['']
            })
        });
    }

    ngOnInit(): void {
        this.loadDropdownData();
        this.checkEditMode();
    }

    private loadDropdownData(): void {
        // Load all dropdown data in parallel
        this.employeeService.getEmployeeFieldOptions()
        .pipe(takeUntil(this.destroy$))
        .subscribe(options => {
            this.accountTypes = options.actions.POST.bank_account_type.choices;
            this.categories = options.actions.POST.category.choices;
        });

        this.employeeService.getShifts({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.shifts = data.results);

        // Load other dropdowns similarly
    }

    private checkEditMode(): void {
        const id = this.route.snapshot.params['id'];
        if (id) {
        this.isEditMode = true;
        this.employeeId = +id;
        this.loadEmployeeData(id);
        } else {
        this.generateEmployeeId();
        }
    }

    private loadEmployeeData(id: number): void {
        this.employeeService.fetchEmployee(id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
            next: (employee) => {
            this.employeeForm.patchValue(this.mapEmployeeToForm(employee));
            },
            error: (error) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to load employee data'
                });
            }
        });
    }

    private generateEmployeeId(): void {
        this.employeeService.getUniqueId()
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => {
            this.employeeForm.patchValue({
            employeeId: data.employee_id,
            deviceEnrollId: data.device_enroll_id
            });
        });
    }

    onSubmit(): void {
        if (this.employeeForm.invalid) {
        return;
    }

    const formData = this.prepareFormData();
    const request$ = this.isEditMode ?
        this.employeeService.updateEmployee(this.employeeId!, formData) :
        this.employeeService.addEmployee(formData);

    request$.pipe(takeUntil(this.destroy$))
        .subscribe({
            next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: `Employee ${this.isEditMode ? 'updated' : 'added'} successfully`
            });
            this.router.navigate(['/employee-master']);
            },
            error: (error) => {
            this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: `Failed to ${this.isEditMode ? 'update' : 'add'} employee`
            });
            }
        });
    }

    private prepareFormData(): FormData {
        const formData = new FormData();
        const formValue = this.employeeForm.value;

        // Append file if exists
        if (formValue.profilePic) {
        formData.append('profile_pic', formValue.profilePic);
        }

        // Append all other form values
        Object.keys(formValue).forEach(key => {
        if (formValue[key] !== null && key !== 'profilePic') {
            if (formValue[key] instanceof Date) {
            formData.append(key, formValue[key].toISOString().split('T')[0]);
            } else if (typeof formValue[key] === 'boolean') {
            formData.append(key, formValue[key] ? '1' : '0');
            } else {
            formData.append(key, formValue[key].toString());
            }
        }
        });

        return formData;
    }

    onFileSelect(event: Event): void {
        const file = (event.target as HTMLInputElement).files?.[0];
        if (file) {
        this.employeeForm.patchValue({ profilePic: file });
        }
    }

    private mapEmployeeToForm(employee: any): Partial<EmployeeForm> {
        return {
            employeeId: employee.employee_id,
            deviceEnrollId: employee.device_enroll_id,
            employeeName: employee.employee_name,
            accessCardNo: employee.access_card_no,
            email: employee.email,
            phoneNo: employee.phone_no,
            pfNo: employee.pf_no,
            esiNo: employee.esi_no,
            insuranceNo: employee.insurance_no,

        // Map other fields similarly
        };
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }
}
