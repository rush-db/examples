import RushDB from "@rushdb/javascript-sdk";
import { NextRequest, NextResponse } from "next/server";

const db = new RushDB(process.env.RUSHDB_API_TOKEN!, {
  url: process.env.RUSHDB_URL!,
});

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    const isEmail =
      typeof email === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    if (!isEmail) {
      return NextResponse.json(
        { error: "Invalid email address" },
        { status: 400 }
      );
    }

    // Check if email already exists in the waitlist
    const existingRecord = await db.records.findOne({
      labels: ["Waitlist"],
      where: {
        email,
      },
    });

    // Save to RushDB
    const record = existingRecord.exists()
      ? existingRecord
      : await db.records.create({
          label: "Waitlist",
          data: { email },
        });

    return NextResponse.json({
      success: true,
      id: record.id(),
    });
  } catch (error) {
    console.error("Waitlist API Error:", error);
    return NextResponse.json(
      { error: "Failed to save email to waitlist" },
      { status: 500 }
    );
  }
}
