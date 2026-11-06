export interface EmployeeSearchParams {
  name?: string;
  minSalary?: string;
  maxSalary?: string;
}

export interface EmployeeDto {
  name: string;
  position: string;
  email: string;
  dob: string;
  salary: number;
}
