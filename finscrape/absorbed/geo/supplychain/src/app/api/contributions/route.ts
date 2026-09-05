import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createContribution } from "@/lib/db/queries";

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json(
        { error: "Authentication required. Sign in with GitHub to contribute." },
        { status: 401 }
      );
    }

    const { treeId, nodeId, type, data } = await req.json();

    if (!treeId || !type) {
      return NextResponse.json(
        { error: "treeId and type are required" },
        { status: 400 }
      );
    }

    const validTypes = ["add_node", "correct_node", "add_company", "report_issue"];
    if (!validTypes.includes(type)) {
      return NextResponse.json(
        { error: `type must be one of: ${validTypes.join(", ")}` },
        { status: 400 }
      );
    }

    const userId = (session.user as { id?: string }).id ?? "unknown";
    await createContribution(userId, treeId, nodeId ?? null, type, data ?? {});

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("[API /contributions] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Contribution failed" },
      { status: 500 }
    );
  }
}
