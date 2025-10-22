import type { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET'])
    return res.status(405).json({ ok: false, message: 'Method Not Allowed' })
  }

  try {
    const result = await db.records.find({ labels: ['ADDRESS'] })
    const data = result.data.map((r: any) => ({ id: r.id(), ...r.data }))
    return res.status(200).json({ ok: true, data })
  } catch (e: any) {
    return res.status(500).json({ ok: false, message: e?.message || 'Error' })
  }
}
