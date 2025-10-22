import type { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/db'

interface OrderPayload {
  createdAt: string
  status: string
  delivery: {
    method: 'Express' | 'Standard'
    status: string
    address: {
      city: string
      street: string
      postalCode: string
      country: string
    }
    addressId?: string
  }
  order_item: Array<{
    id: string
    name: string
    price: number
    qty: number
    subtotal: number
  }>
  total: number
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'POST') {
    // Begin a transaction to ensure all related records are created atomically
    const tx = await db.tx.begin()

    try {
      const body = (req.body as OrderPayload) || ({} as OrderPayload)

      /* OPTION 1: importJson */

      await db.records.importJson({
        label: 'ORDER',
        data: body,
        options: {
          capitalizeLabels: true,
          suggestTypes: true,
          convertNumericValuesToNumbers: true,
        },
      })

      /* OPTION 2: atomic records creation */

      // 1) Create ORDER record
      // const orderRecord = await db.records.create(
      //   {
      //     label: 'ORDER',
      //     data: {
      //       createdAt: body.createdAt,
      //       status: body.status,
      //       total: body.total,
      //     },
      //   },
      //   tx
      // )

      // // 2) Create DELIVERY record
      // const deliveryRecord = await db.records.create(
      //   {
      //     label: 'DELIVERY',
      //     data: {
      //       method: body.delivery.method,
      //       status: body.delivery.status,
      //     },
      //   },
      //   tx
      // )

      // if (body.delivery.address) {
      //   // 3) Optionally create ADDRESS record
      //   const addressRecord = await db.records.create(
      //     {
      //       label: 'ADDRESS',
      //       data: {
      //         city: body.delivery.address.city,
      //         street: body.delivery.address.street,
      //         postalCode: body.delivery.address.postalCode,
      //         country: body.delivery.address.country,
      //       },
      //     },
      //     tx
      //   )

      //   // 4a) Link DELIVERY -> ADDRESS
      //   await deliveryRecord.attach(addressRecord, {}, tx)
      // } else if (body.delivery.addressId) {
      //   // 4b) Or link DELIVERY -> existing ADDRESS by ID
      //   await deliveryRecord.attach(body.delivery.addressId, {}, tx)
      // }

      // // 5) Create ORDER_ITEM records (one per cart item)
      // const itemRecords = await db.records.createMany(
      //   {
      //     label: 'ORDER_ITEM',
      //     data: body.order_item,
      //     options: { convertNumericValuesToNumbers: true, returnResult: true },
      //   },
      //   tx
      // )

      // // 6) Link ORDER -> DELIVERY and ORDER_ITEMs
      // await orderRecord.attach([deliveryRecord, ...itemRecords.data], {}, tx)

      // // 7) Commit transaction
      // await tx.commit()

      return res.status(201).json({ ok: true })
    } catch (e: any) {
      await tx.rollback()
      return res.status(500).json({ ok: false, message: e?.message || 'Error' })
    }
  }
  if (req.method === 'GET') {
    try {
      const ordersRes = await db.records.find({
        labels: ['ORDER'],

        /** Nested aggregations
         * Docs:
         * https://docs.rushdb.com/concepts/search/aggregations#1-collecting-nested-records
         * */

        // where: {
        //   DELIVERY: {
        //     $alias: '$delivery',
        //     ADDRESS: {
        //       $alias: '$address',
        //     },
        //   },
        // },
        // aggregate: {
        //   delivery: {
        //     fn: 'collect',
        //     alias: '$delivery',
        //     aggregate: {
        //       address: { fn: 'collect', alias: '$address' },
        //     },
        //   },
        // },
      })

      const data = ordersRes.data.map((o) => ({
        id: o.id(),
        ...o.data,
        // delivery: {
        //   ...o.data.delivery[0],
        //   address: o.data.delivery[0].address[0],
        // },
      }))
      return res.status(200).json({ ok: true, data })
    } catch (e: any) {
      return res.status(500).json({ ok: false, message: e?.message || 'Error' })
    }
  }
  res.setHeader('Allow', ['GET', 'POST'])
  return res.status(405).json({ ok: false, message: 'Method Not Allowed' })
}
