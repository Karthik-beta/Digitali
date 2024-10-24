import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SharedService {

    private APIUrl = environment.APIUrl;



  constructor(private http:HttpClient) { }


  // Config
  // Updated at
  getUpdatedat():Observable<any[]>{
    return this.http.get<any[]>(`${this.APIUrl}/updated_at/`);
  }

  // Resource

  // Employee Master
  deleteEmployee(id: number){
    return this.http.delete(this.APIUrl+'/employee/'+id);
  }


    // Company Resource
    // List and Create
    getCompanies(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/company/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addCompany(company: any): Observable<any> {
    return this.http.post<any>(`${this.APIUrl}/company/`, company);
    }

    updateCompany(company: any): Observable<any> {
    return this.http.put<any>(`${this.APIUrl}/company/${company.id}/`, company);
    }

    deleteCompany(id: number): Observable<any> {
        return this.http.delete<any>(`${this.APIUrl}/company/${id}/`);
    }

    // Location Resource
    // List and Create
    getLocations(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/location/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addLocation(location: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/location/`, location);
    }

    updateLocation(location: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/location/${location.id}/`, location);
    }

    deleteLocation(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/location/${id}/`);
    }

    // Department Resource
    // List and Create
    getDepartments(params: any): Observable<any> {
      let httpParams = new HttpParams();

    for (const key in params) {
      if (params.hasOwnProperty(key)) {
        httpParams = httpParams.append(key, params[key]);
      }
    }
      return this.http.get<any[]>(`${this.APIUrl}/department/`, { params: httpParams });
    }

    // Retrieve, Update, Destroy
    addDepartment(department: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/department/`, department);
    }

    updateDepartment(department: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/department/${department.id}/`, department);
    }

    deleteDepartment(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/department/${id}/`);
    }

    // Designation Resource
    // List and Create
    getDesignations(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/designation/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addDesignation(designation: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/designation/`, designation);
    }

    updateDesignation(designation: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/designation/${designation.id}/`, designation);
    }

    deleteDesignation(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/designation/${id}/`);
    }

    // Divisions Resource
    // List and Create
    getDivisions(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/division/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addDivision(division: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/division/`, division);
    }

    updateDivision(division: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/division/${division.id}/`, division);
    }

    deleteDivision(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/division/${id}/`);
    }

    // SubDivision Resource
    // List and Create
    getSubDivisions(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/subdivision/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addSubDivision(subdivision: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/subdivision/`, subdivision);
    }

    updateSubDivision(subdivision: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/subdivision/${subdivision.id}/`, subdivision);
    }

    deleteSubDivision(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/subdivision/${id}/`);
    }

    // Shift Resource
    // List and Create
    getShifts(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/shift/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addShift(shift: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/shift/`, shift);
    }

    updateShift(shift: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/shift/${shift.id}/`, shift);
    }

    deleteShift(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/shift/${id}/`);
    }

    // Shopfloor Resource
    // List and Create
    getShopfloors(params: any): Observable<any> {
      let queryParams = new HttpParams();
      for (const key in params) {
        if (params.hasOwnProperty(key)) {
          queryParams = queryParams.append(key, params[key]);
        }
      }
      return this.http.get<any[]>(`${this.APIUrl}/shopfloor/`, { params: queryParams });
    }

    // Retrieve, Update, Destroy
    addShopfloor(shopfloor: any): Observable<any> {
      return this.http.post<any>(`${this.APIUrl}/shopfloor/`, shopfloor);
    }

    updateShopfloor(shopfloor: any): Observable<any> {
      return this.http.put<any>(`${this.APIUrl}/shopfloor/${shopfloor.id}/`, shopfloor);
    }

    deleteShopfloor(id: number): Observable<any> {
      return this.http.delete<any>(`${this.APIUrl}/shopfloor/${id}/`);
    }








    getEmployeeList(params: any): Observable<any> {
        let httpParams = new HttpParams();

        for (const key in params) {
          if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
          }
        }

        return this.http.get(`${this.APIUrl}/employee/`, { params: httpParams });
    }

    addEmployee(formData: any){
        return this.http.post<any>(`${this.APIUrl}/employee/`, formData);
    }


  // Method to retrieve options using OPTIONS HTTP method
  getEmployeeFieldOptions(): Observable<any> {
    return this.http.options(`${this.APIUrl}/employee/`);
  }

  getUniqueId(): Observable<any> {
    return this.http.get(`${this.APIUrl}/unique_id/`);
  }

  postEmployeeId(requestBody: any): Observable<any> {
    return this.http.post(`${this.APIUrl}/employee_id/`, requestBody);
  }

  updateEmployee(id: number, formData: any): Observable<any> {
    return this.http.put(`${this.APIUrl}/employee/${id}/`, formData);
  }

  fetchEmployee(id: number): Observable<any> {
    return this.http.get(`${this.APIUrl}/employee/${id}/`);
  }

  getAttendanceList(params: any): Observable<any> {
    let httpParams = new HttpParams();

    for (const key in params) {
      if (params.hasOwnProperty(key)) {
        httpParams = httpParams.append(key, params[key]);
      }
    }

    return this.http.get(`${this.APIUrl}/attendance/`, { params: httpParams });
  }

  // Download attendance report
  downloadAttendanceReport(params: any): Observable<any> {

    let httpParams = new HttpParams();

    for (const key in params) {
      if (params.hasOwnProperty(key)) {
        httpParams = httpParams.append(key, params[key]);
      }
    }

    return this.http.get(`${this.APIUrl}/attendance/export/`, {
        params: httpParams,
        responseType: 'blob' as 'json', // Set the response type to 'blob' for binary data
    });
  }

    // Attendance Metrics
    getAttendanceMetrics(): Observable<any> {
        return this.http.get(`${this.APIUrl}/attendance/metrics/daily/`);
    }

    getAttendanceMonthlyMetrics(): Observable<any> {
        return this.http.get(`${this.APIUrl}/attendance/metrics/monthly/`);
    }

    // Logs Resource
    getLogList(params: any): Observable<any> {
        let httpParams = new HttpParams();

        for (const key in params) {
          if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
          }
        }

        return this.http.get(`${this.APIUrl}/logs/`, { params: httpParams });
    }

    postLog(formData: any): Observable<any> {
        return this.http.post(`${this.APIUrl}/logs/`, formData);
    }

    updateLog(id: number, formData: any): Observable<any> {
        return this.http.put(`${this.APIUrl}/logs/${id}/`, formData);
    }

    deleteLog(id: number): Observable<any> {
        return this.http.delete(`${this.APIUrl}/logs/${id}/`);
    }

    // Get Employee Dropdown
    getEmployeeDropdown(): Observable<any> {
        return this.http.get(`${this.APIUrl}/employee/dropdown/`);
    }

    // Download Employee monthly report
    downloadEmployeeMonthlyReport(params: any): Observable<any> {

        let httpParams = new HttpParams();

        for (const key in params) {
          if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
          }
        }

        return this.http.get(`${this.APIUrl}/attendance/employee/`, {
            params: httpParams,
            responseType: 'blob' as 'json', // Set the response type to 'blob' for binary data
        });
    }

    downloadAllEmployeeMonthlyReport(params: any): Observable<any> {

        let httpParams = new HttpParams();

        for (const key in params) {
          if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
          }
        }

        return this.http.get(`${this.APIUrl}/attendance/export/allemployees/`, {
            params: httpParams,
            responseType: 'blob' as 'json', // Set the response type to 'blob' for binary data
        });
    }

    getMandaysAttendanceList(params: any): Observable<any> {
        let httpParams = new HttpParams();

        for (const key in params) {
          if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
          }
        }

        return this.http.get(`${this.APIUrl}/attendance/mandays/`, { params: httpParams });
    }

    downloadMandaysAttendanceReport(params: any): Observable<any> {

        let httpParams = new HttpParams();

        for (const key in params) {
        if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
        }
        }

        return this.http.get(`${this.APIUrl}/attendance/mandays/report/`, {
            params: httpParams,
            responseType: 'blob' as 'json', // Set the response type to 'blob' for binary data
        });
    }

    downloadMandaysWorkedReport(params: any): Observable<any> {

        let httpParams = new HttpParams();

        for (const key in params) {
        if (params.hasOwnProperty(key)) {
            httpParams = httpParams.append(key, params[key]);
        }
        }

        return this.http.get(`${this.APIUrl}/attendance/mandays/work_report/`, {
            params: httpParams,
            responseType: 'blob' as 'json', // Set the response type to 'blob' for binary data
        });
    }

    getLogReport(params: any): Observable<any> {
        let httpParams = new HttpParams();

        for (const key in params) {
            if (params.hasOwnProperty(key)) {
                httpParams = httpParams.append(key, params[key]);
            }
            }

        return this.http.get(`${this.APIUrl}/logs/`, { params: httpParams });
    }

}
