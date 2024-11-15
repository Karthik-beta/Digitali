import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { access } from 'fs';
import { MessageService } from 'primeng/api';
import { InputSwitchModule } from 'primeng/inputswitch';
import { Subject, takeUntil } from 'rxjs';
import { SharedService } from 'src/app/shared.service';

interface EmployeeForm {
    profile_pic: File | null;
    employee_id: string;
    employee_name: string;
    device_enroll_id: string;
    email: string;
    phone_no: number | null;
    pf_no: string;
    esi_no: string;
    insurance_no: string;

    bank_name: string;
    bank_branch: string;
    bank_account_no: string;
    bank_account_name: string;
    bank_account_type: string | null;
    ifsc_code: string;

    category: string | null;
    job_type: string | null;
    date_of_joining: string | null;
    date_of_leaving: string | null;
    job_status: string | null;
    reason_for_leaving: string;

    emergency_contact_name: string;
    emergency_contact_no: number | null;
    marital_status: string | null;
    spouse_name: string;
    blood_group: string;
    date_of_birth: string | null;
    country_name: string;
    country_code: string;
    uid_no: string;
    pan_no: string;
    voter_id: string;
    driving_license: string;
    gender: string | null;
    present_address: string;
    permanent_address: string;
    additional_info: string;
    graduation: string;
    course_type: string | null;
    course: string;
    place_of_graduation: string;
    aggregate: number | null;
    year_of_graduation: number | null;
    auto_shift: boolean;
    first_weekly_off: string | null;
    second_weekly_off: string | null;
    week_off_effective_date: string | null;
    flexi_time: boolean;
    consider_late_entry: boolean;
    consider_early_exit: boolean;
    consider_extra_hours_worked: boolean;
    consider_late_entry_on_holiday: boolean;
    consider_early_exit_on_holiday: boolean;
    consider_extra_hours_worked_on_holiday: boolean;
    search_next_day: boolean;
    company: number | null;
    location: number | null;
    department: number | null;
    designation: number | null;
    division: number | null;
    subdivision: number | null;
    shopfloor: number | null;
    reporting_manager: number | null;
    alt_reporting_manager: number | null;
    shift: number | null;
}

interface UploadEvent {
    originalEvent: Event;
    files: File[];
}

interface ChoiceOption {
    value: string;
    display_name: string;
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
    uploadedFiles: any[] = [];
    activeStepperNumber: number | undefined = 3;
    private destroy$ = new Subject<void>();

    punchOutOptions = [
        { label: "Consider next day's first punch at out time", value: 'first_punch' },
        { label: "Consider next day's punch max search", value: 'max_search' }
    ];

    // Dropdown options
    accountTypes: any[] = [];
    categories: ChoiceOption[] = [];
    jobTypes: ChoiceOption[] = [];
    jobStatusOptions: ChoiceOption[] = [];
    maritalStatusOptions: any[] = [];
    genderOptions: ChoiceOption[] = [];
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
                company: [null, Validators.required],
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
                jobStatus: [null],
                reportingManager: [null],
                altReportingManager: [null],
                reasonForLeaving: ['']
            }),

            // Work Configuration as nested form group
            workConfig: this.fb.group({
                shift: [null],
                autoShift: [true],
                flexiTime: [false],
                considerLateEntry: [true],
                considerEarlyExit: [true],
                considerExtraHoursWorked: [true],
                considerLateEntryOnHoliday: [true],
                considerEarlyExitOnHoliday: [true],
                considerExtraHoursWorkedOnHoliday: [true],
                searchNextDay: [true]
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
            this.categories = options.actions.POST.category.choices
            this.jobTypes = options.actions.POST.job_type.choices
            // this.jobTypes = options.actions.POST.job_type.choices.map((choice: any) => ({
            //     value: choice.value,
            //     display_name: choice.display_name
            //   }));
            this.jobStatusOptions = options.actions.POST.job_status.choices;
            this.maritalStatusOptions = options.actions.POST.marital_status.choices;
            this.genderOptions = options.actions.POST.gender.choices;
        });

        this.employeeService.getShifts({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.shifts = data.results);

        this.employeeService.getCompanies({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.companies = data.results);

        this.employeeService.getLocations({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.locations = data.results);

        this.employeeService.getDepartments({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.departments = data.results);

        this.employeeService.getDesignations({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.designations = data.results);

        this.employeeService.getDivisions({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.divisions = data.results);

        this.employeeService.getSubDivisions({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.subDivisions = data.results);

        this.employeeService.getShopfloors({ page: 1, page_size: 1000 })
        .pipe(takeUntil(this.destroy$))
        .subscribe(data => this.shopfloors = data.results);

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
    //     if (this.employeeForm.invalid) {
    //     return;
    // }
    console.log(this.employeeForm.value);

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

        // The company ID will be available in formValue.officialDetails.company
        if (formValue.officialDetails.company) {
            formData.append('company', formValue.officialDetails.company);
        }

        if (formValue.officialDetails.location) {
            formData.append('location', formValue.officialDetails.location);
        }

        if (formValue.officialDetails.department) {
            formData.append('department', formValue.officialDetails.department);
        }

        if (formValue.officialDetails.designation) {
            formData.append('designation', formValue.officialDetails.designation);
        }

        if (formValue.officialDetails.division) {
            formData.append('division', formValue.officialDetails.division);
        }

        if (formValue.officialDetails.subdivision) {
            formData.append('subdivision', formValue.officialDetails.subdivision);
        }

        if (formValue.officialDetails.shopfloor) {
            formData.append('shopfloor', formValue.officialDetails.shopfloor);
        }

        if (formValue.officialDetails.reportingManager) {
            formData.append('reporting_manager', formValue.officialDetails.reportingManager);
        }

        if (formValue.officialDetails.altReportingManager) {
            formData.append('alt_reporting_manager', formValue.officialDetails.altReportingManager);
        }

        if (formValue.officialDetails.category) {
            formData.append('category', formValue.officialDetails.category);
        }

        if (formValue.officialDetails.jobType) {
            formData.append('job_type', formValue.officialDetails.jobType);
        }

        if (formValue.officialDetails.jobStatus) {
            formData.append('job_status', formValue.officialDetails.jobStatus);
        }

        if (formValue.personalDetails.gender) {
            formData.append('gender', formValue.personalDetails.gender)
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
        console.log(employee);
        return {
            // employeeId: employee.employee_id,
            // deviceEnrollId: employee.device_enroll_id,
            // employeeName: employee.employee_name,
            // accessCardNo: employee.access_card_no,
            // email: employee.email,
            // phoneNo: employee.phone_no,
            // pfNo: employee.pf_no,
            // esiNo: employee.esi_no,
            // insuranceNo: employee.insurance_no,

            // bankDetails: {
            //     bankName: employee.bank_name,
            //     bankBranch: employee.bank_branch,
            //     bankAccountNo: employee.bank_account_no,
            //     bankAccountName: employee.bank_account_name,
            //     bankAccountType: employee.bank_account_type,
            //     ifscCode: employee.ifsc_code,
            // },

            // officialDetails: {
            //     company: employee.company,
            //     location: employee.location,
            //     category: employee.category,
            //     department: employee.department,
            //     designation: employee.designation,
            //     division: employee.division,
            //     subdivision: employee.subdivision,
            //     shopfloor: employee.shopfloor,
            //     jobType: employee.job_type,
            //     dateOfJoining: new Date(employee.date_of_joining),
            //     dateOfLeaving: new Date(employee.date_of_leaving),
            //     jobStatus: employee.job_status,
            //     reportingManager: employee.reporting_manager,
            //     altReportingManager: employee.alt_reporting_manager,
            //     reasonForLeaving: employee.reason_for_leaving,
            // },

            // workConfig: {
            // shift: employee.shift,
            // autoShift: employee.auto_shift,
            // flexiTime: employee.flexi_time,
            // considerLateEntry: employee.consider_late_entry,
            // considerEarlyExit: employee.consider_early_exit,
            // considerExtraHoursWorked: employee.consider_extra_hours_worked,
            // considerLateEntryOnHoliday: employee.consider_late_entry_on_holiday,
            // considerEarlyExitOnHoliday: employee.consider_early_exit_on_holiday,
            // considerExtraHoursWorkedOnHoliday: employee.consider_extra_hours_worked_on_holiday,
            // searchNextDay: employee.search_next_day,
            // },

            // personalDetails: {
            //     emergencyContactName: employee.emergency_contact_name,
            //     emergencyContactNo: employee.emergency_contact_no,
            //     maritalStatus: employee.marital_status,
            //     spouseName: employee.spouse_name,
            //     bloodGroup: employee.blood_group,
            //     dateOfBirth: new Date(employee.date_of_birth),
            //     countryName: employee.country_name,
            //     countryCode: employee.country_code,
            //     uidNo: employee.uid_no,
            //     panNo: employee.pan_no,
            //     voterId: employee.voter_id,
            //     drivingLicense: employee.driving_license,
            //     gender: employee.gender,
            //     presentAddress: '',
            //     permanentAddress: ''
            // },

            // Map other fields similarly
        };

    }

    onUpload(event:UploadEvent) {
        for(let file of event.files) {
            this.uploadedFiles.push(file);
        }

        this.messageService.add({severity: 'info', summary: 'File Uploaded', detail: ''});
    }



    fileName = '';

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }
}
