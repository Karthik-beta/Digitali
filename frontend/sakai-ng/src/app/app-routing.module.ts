import { RouterModule } from '@angular/router';
import { NgModule } from '@angular/core';
import { NotfoundComponent } from './demo/components/notfound/notfound.component';
import { AppLayoutComponent } from "./layout/app.layout.component";
import { authGuard } from './guards/auth.guard';

import { ShiftSkillComponent } from './components/resource/resource-dashboard/shift-skill/shift-skill.component';
import { ConfigComponent } from './components/configuration/config/config.component';
import { EmployeeMasterComponent } from './components/resource/employee-master/employee-master.component';
import { DailyReportComponent } from './components/resource/daily-report/daily-report.component';
import { ShiftStrengthComponent } from './components/resource/resource-dashboard/shift-strength/shift-strength.component';
import { EvacuationComponent } from './components/resource/resource-dashboard/evacuation/evacuation.component';
import { AddEditEmployeeComponent } from './components/resource/employee-master/add-edit-employee/add-edit-employee.component';
import { MonthlyInOutComponent } from './components/resource/monthly-in-out/monthly-in-out.component';
import { MissedPunchComponent } from './components/resource/attendance-reg/missed-punch/missed-punch.component';

@NgModule({
    imports: [
        RouterModule.forRoot([
            // { path: '', redirectTo: 'auth/login', pathMatch: 'full' },
            {
                path: '', component: AppLayoutComponent,
                children: [
                    { path: '', loadChildren: () => import('./demo/components/dashboard/dashboard.module').then(m => m.DashboardModule), canActivate: [authGuard] },
                    { path: 'uikit', loadChildren: () => import('./demo/components/uikit/uikit.module').then(m => m.UIkitModule), canActivate: [authGuard] },
                    { path: 'utilities', loadChildren: () => import('./demo/components/utilities/utilities.module').then(m => m.UtilitiesModule), canActivate: [authGuard] },
                    { path: 'documentation', loadChildren: () => import('./demo/components/documentation/documentation.module').then(m => m.DocumentationModule), canActivate: [authGuard] },
                    { path: 'blocks', loadChildren: () => import('./demo/components/primeblocks/primeblocks.module').then(m => m.PrimeBlocksModule), canActivate: [authGuard] },
                    { path: 'pages', loadChildren: () => import('./demo/components/pages/pages.module').then(m => m.PagesModule), canActivate: [authGuard] },

                    { path: 'shift_skill', component: ShiftSkillComponent, canActivate: [authGuard] },

                    // Resource
                    { path: 'employee_master', component: EmployeeMasterComponent, canActivate: [authGuard] },
                    { path: 'add_employee', component: AddEditEmployeeComponent, canActivate: [authGuard] },
                    { path: 'view_edit_employee/:id', component: AddEditEmployeeComponent, canActivate: [authGuard] },
                    { path: 'daily_report', component: DailyReportComponent, canActivate: [authGuard] },
                    { path: 'Monthly_In_Out', component: MonthlyInOutComponent, canActivate: [authGuard] },
                    { path: 'shift_strength', component: ShiftStrengthComponent, canActivate: [authGuard] },
                    { path: 'evacuation', component: EvacuationComponent, canActivate: [authGuard] },
                    { path: 'missed_punch', component: MissedPunchComponent, canActivate: [authGuard] },


                    // Configuration
                    { path: 'configuration', component: ConfigComponent, canActivate: [authGuard] },
                ]
            },
            { path: 'auth', loadChildren: () => import('./demo/components/auth/auth.module').then(m => m.AuthModule) },
            { path: 'landing', loadChildren: () => import('./demo/components/landing/landing.module').then(m => m.LandingModule) },
            { path: 'notfound', component: NotfoundComponent },
            { path: '**', redirectTo: '/notfound' },
        ], { scrollPositionRestoration: 'enabled', anchorScrolling: 'enabled', onSameUrlNavigation: 'reload' })
    ],
    exports: [RouterModule]
})
export class AppRoutingModule {
}
