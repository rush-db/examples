import { Request, Response } from 'express';
import { db } from '../db';
import { EmployeeDto, EmployeeSearchParams } from '../types/employee';

export async function createEmployee(req: Request, res: Response) {
  const tx = await db.tx.begin();

  try {
    const { departmentId } = req.params;

    const employeeData: EmployeeDto[] = req.body;

    const result = await db.records.createMany('EMPLOYEE', employeeData);
    await db.records.attach(departmentId, result, {}, tx);
    await tx.commit();

    return res.json(result.data);
  } catch (error) {
    console.error('Error creating employee:', error);
    await tx.rollback();
    return res.status(500).json({ error: 'Failed to create employee' });
  }
}

export async function updateEmployee(req: Request, res: Response) {
  try {
    const { employeeId } = req.params;
    const updateData: EmployeeDto = req.body;

    const result = await db.records.update(employeeId, updateData);
    return res.json(result.data);
  } catch (error) {
    console.error('Error updating employee:', error);
    return res.status(500).json({ error: 'Failed to update employee' });
  }
}

export async function deleteEmployee(req: Request, res: Response) {
  try {
    const { employeeId } = req.params;
    const result = await db.records.deleteById(employeeId);
    return res.json(result);
  } catch (error) {
    console.error('Error deleting employee:', error);
    return res.status(500).json({ error: 'Failed to delete employee' });
  }
}

export async function getAllEmployeesByDepartment(req: Request, res: Response) {
  try {
    const { departmentId } = req.params;

    const employees = await db.records.find({
      labels: ['EMPLOYEE'],
      where: {
        DEPARTMENT: {
          $id: departmentId,
        },
      },
    });

    return res.json(employees.data);
  } catch (error) {
    console.error('Error retrieving employees:', error);
    return res.status(500).json({ error: 'Failed to retrieve employees' });
  }
}

export async function getEmployeeById(req: Request, res: Response) {
  try {
    const { employeeId } = req.params;

    const employee = await db.records.findUniq('EMPLOYEE', {
      where: {
        $id: employeeId,
      },
    });

    if (!employee) {
      return res.status(404).json({ error: 'Employee not found' });
    }

    return res.json(employee);
  } catch (error) {
    console.error('Error retrieving employee:', error);
    return res.status(500).json({ error: 'Failed to retrieve employee' });
  }
}

export async function searchEmployee(
  req: Request,
  res: Response
): Promise<Response> {
  try {
    const { name, minSalary, maxSalary } = req.query as EmployeeSearchParams;
    const whereClause: any = {};

    if (name) {
      whereClause.name = { $contains: name };
    }

    if (minSalary || maxSalary) {
      whereClause.salary = {};
      if (minSalary) {
        whereClause.salary.$gte = Number(minSalary);
      }
      if (maxSalary) {
        whereClause.salary.$lte = Number(maxSalary);
      }
    }

    const result = await db.records.find('EMPLOYEE', {
      labels: ['EMPLOYEE'],
      where: whereClause,
    });

    return res.json(result.data);
  } catch (error) {
    console.error('Error searching employees:', error);
    return res.status(500).json({ error: 'Failed to search employees' });
  }
}
