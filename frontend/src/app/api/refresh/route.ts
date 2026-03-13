import { NextResponse } from "next/server";

export async function POST() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!base) {
    return NextResponse.json(
      { error: "Missing NEXT_PUBLIC_API_BASE_URL" },
      { status: 500 }
    );
  }

  const backendUrl = `${base.replace(/\/$/, "")}/refresh`;

  try {
    const res = await fetch(backendUrl, {
      method: "POST",
      cache: "no-store",
    });

    const text = await res.text();

    return new NextResponse(text, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Failed to refresh stories." },
      { status: 500 }
    );
  }
}