import { Request, Response } from 'express';
import { db } from '../db';
import { DepartmentDto } from '../types/department';

export async function createDepartment(req: Request, res: Response) {
  const tx = await db.tx.begin();

  try {
    const { companyId } = req.params;

    const departmentData: DepartmentDto = req.body;

    console.log(req.params);
    const result = await db.records.create('DEPARTMENT', departmentData, tx);
    await db.records.attach(companyId, result, {}, tx);

    await tx.commit();

    return res.json(result);
  } catch (error) {
    console.error('Error creating department:', error);
    await tx.rollback();
    return res.status(500).json({ error: 'Failed to create department' });
  }
}

export async function updateDepartment(req: Request, res: Response) {
  try {
    const { departmentId } = req.params;
    const updateData: DepartmentDto = req.body;

    const result = await db.records.update(departmentId, updateData);
    return res.json(result.data);
  } catch (error) {
    console.error('Error updating department:', error);
    return res.status(500).json({ error: 'Failed to update department' });
  }
}

export async function deleteDepartment(req: Request, res: Response) {
  try {
    const { departmentId } = req.params;
    const result = await db.records.deleteById(departmentId);
    return res.json(result);
  } catch (error) {
    console.error('Error deleting department:', error);
    return res.status(500).json({ error: 'Failed to delete department' });
  }
}

export async function getAllDepartmentsByCompany(req: Request, res: Response) {
  try {
    const { companyId } = req.params;

    // @ts-expect-error
    const departments = await db.records.find({
      labels: ['DEPARTMENT', 'COMPANY'],
      where: {
        COMPANY: {
          $id: companyId,
        },
      },
    });

    return res.json(departments.data);
  } catch (error) {
    console.error('Error retrieving departments:', error);
    return res.status(500).json({ error: 'Failed to retrieve departments' });
  }
}

export async function getDepartmentById(req: Request, res: Response) {
  try {
    const { departmentId } = req.params;

    const department = await db.records.findUniq('DEPARTMENT', {
      where: {
        $id: departmentId,
      },
    });

    if (!department.data) {
      return res.status(404).json({ error: 'Department not found' });
    }

    return res.json(department);
  } catch (error) {
    console.error('Error retrieving department:', error);
    return res.status(500).json({ error: 'Failed to retrieve department' });
  }
}

export async function getDepartmentStatsById(req: Request, res: Response) {
  try {
    const { departmentId } = req.params;

    // @ts-expect-error
    const department = await db.records.findUniq('DEPARTMENT', {
      where: {
        $id: departmentId,
        EMPLOYEE: {
          $alias: '$emp',
        },
      },
      aggregate: {
        activeEmployees: {
          fn: 'count',
          alias: '$emp',
        },
        maxSalary: {
          fn: 'max',
          field: 'salary',
          alias: '$emp',
        },
        avgSalary: {
          fn: 'avg',
          field: 'salary',
          alias: '$emp',
          precision: 2,
        },
        EMPLOYEE: {
          fn: 'collect',
          alias: '$emp',
          orderBy: {
            salary: 'desc',
          },
        },
      },
    });

    if (!department.data) {
      return res.status(404).json({ error: 'Department not found' });
    }

    return res.json(department);
  } catch (error) {
    console.error('Error retrieving department:', error);
    return res.status(500).json({ error: 'Failed to retrieve department' });
  }
}
