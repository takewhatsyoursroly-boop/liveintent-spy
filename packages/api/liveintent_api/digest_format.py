def format_digest_message(top_by_vertical: dict[str, list[tuple[str, int]]], *, window_label: str) -> str:
    if not top_by_vertical:
        return f"*LiveIntent Spy — {window_label}*\n\nNo activity in this window."
    parts = [f"*LiveIntent Spy — {window_label}*", ""]
    for vert in sorted(top_by_vertical.keys()):
        parts.append(f"_{vert}_")
        for domain, count in top_by_vertical[vert]:
            parts.append(f"  • `{domain}` — {count} impressions")
        parts.append("")
    return "\n".join(parts).rstrip()
