import type { NextApiRequest, NextApiResponse } from 'next'
import type { SearchQuery } from '@rushdb/javascript-sdk'
import { db } from '@/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST'])
    return res.status(405).json({ ok: false, message: 'Method Not Allowed' })
  }

  const { id } = req.query
  const propId = Array.isArray(id) ? id[0] : id
  if (!propId) return res.status(400).json({ ok: false, message: 'Missing id' })

  try {
    const args = (req.body as SearchQuery) || {}
    const result: any = await db.properties.values(propId, args as any)
    const data = result?.data ?? result ?? []
    return res.status(200).json({ ok: true, data })
  } catch (e: any) {
    return res.status(500).json({ ok: false, message: e?.message || 'Error' })
  }
}
