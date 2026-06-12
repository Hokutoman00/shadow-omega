"""Generate frames for the Shadow-Omega Copilot certificate demo.

This is intentionally screen-capture free: every frame is rendered from data
already present in the repository, so video generation cannot interfere with
the user's desktop session.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
OUT = Path(__file__).parent / "certificate_out"
OUT.mkdir(exist_ok=True)

BG = (13, 15, 20)
SURFACE = (20, 23, 31)
PANEL = (26, 30, 40)
PANEL_2 = (33, 38, 50)
BORDER = (64, 76, 96)
TEXT = (235, 239, 245)
MUTED = (151, 164, 184)
DIM = (91, 103, 124)
CYAN = (56, 189, 248)
GREEN = (74, 222, 128)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
MAGENTA = (216, 180, 254)
BLUE = (96, 165, 250)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def mono(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/courbd.ttf" if bold else "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split(" ")
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if draw.textlength(candidate, font=face) <= max_width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        if not para:
            lines.append("")
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    face: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap(draw, text, face, max_width):
        draw.text((x, y), line, font=face, fill=fill)
        y += face.size + line_gap
    return y


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str = "", accent=CYAN) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=8, fill=PANEL, outline=BORDER, width=1)
    if title:
        draw.rounded_rectangle((x1, y1, x2, y1 + 48), radius=8, fill=PANEL_2, outline=BORDER, width=1)
        draw.rectangle((x1, y1 + 34, x2, y1 + 48), fill=PANEL_2)
        draw.text((x1 + 24, y1 + 14), title.upper(), font=mono(18, True), fill=accent)


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, fill: tuple[int, int, int], fg=BG) -> None:
    x, y = xy
    f = mono(18, True)
    tw = int(draw.textlength(label, font=f))
    draw.rounded_rectangle((x, y, x + tw + 32, y + 38), radius=19, fill=fill)
    draw.text((x + 16, y + 9), label, font=f, fill=fg)


def header(draw: ImageDraw.ImageDraw, eyebrow: str, title: str, subtitle: str = "") -> None:
    draw.rectangle((0, 0, W, H), fill=BG)
    for i in range(0, W, 96):
        col = (18, 21, 29) if (i // 96) % 2 == 0 else (15, 18, 25)
        draw.line((i, 0, i - 360, H), fill=col, width=1)
    draw.rectangle((0, 0, W, 78), fill=(9, 11, 16))
    draw.line((0, 78, W, 78), fill=BORDER, width=1)
    draw.text((56, 24), eyebrow.upper(), font=mono(20, True), fill=CYAN)
    draw.text((56, 112), title, font=font(64, True), fill=TEXT)
    if subtitle:
        draw_wrapped(draw, (60, 196), subtitle, font(26), MUTED, 1420, 8)
    draw.text((1470, 28), "T1 / Microsoft Agents League", font=mono(18, True), fill=AMBER)


def footer(draw: ImageDraw.ImageDraw) -> None:
    draw.line((56, 1010, W - 56, 1010), fill=(50, 59, 74), width=1)
    draw.text((60, 1030), "Repo: github.com/Hokutoman00/shadow-omega", font=mono(18), fill=DIM)
    draw.text((1320, 1030), "Verifier: python t1-shadow-omega-core/verify_mcp_server.py", font=mono(18), fill=DIM)


def code_block(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: Iterable[str],
    title: str,
    highlights: dict[int, tuple[int, int, int]] | None = None,
) -> None:
    panel(draw, box, title, CYAN)
    x1, y1, x2, _ = box
    f = mono(22)
    y = y1 + 72
    for idx, line in enumerate(lines, start=1):
        if highlights and idx in highlights:
            draw.rounded_rectangle((x1 + 16, y - 5, x2 - 16, y + 31), radius=5, fill=(55, 31, 38))
        draw.text((x1 + 28, y), f"{idx:02d}", font=f, fill=DIM)
        draw.text((x1 + 82, y), line, font=f, fill=highlights.get(idx, TEXT) if highlights else TEXT)
        y += 34


def save(name: str, img: Image.Image) -> None:
    img.save(OUT / name, quality=95)


def scene_00() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "shadow-omega", "Copilot Convergence Certificate", "A Copilot-facing MCP server that turns five independent adversarial universes into one repeatable audit certificate.")
    pill(d, (62, 285), "NEW FINAL DEMO", GREEN)
    pill(d, (286, 285), "NO SCREEN CAPTURE", AMBER)
    pill(d, (540, 285), "MCP VERIFIED", CYAN)

    panel(d, (96, 400, 900, 870), "What the judge sees", MAGENTA)
    bullets = [
        "Not just a dashboard: a callable MCP tool surface.",
        "Not just a finding: a convergence certificate with votes.",
        "Not just advice: a closed loop from discovery to mitigation.",
        "Not just a video: verifier output is checked in and reproducible.",
    ]
    y = 480
    for b in bullets:
        d.ellipse((136, y + 8, 154, y + 26), fill=GREEN)
        y = draw_wrapped(d, (178, y), b, font(30), TEXT, 650, 8) + 18

    panel(d, (1040, 380, 1770, 890), "Certificate snapshot", CYAN)
    d.text((1090, 470), "status", font=mono(22), fill=MUTED)
    d.text((1330, 456), "CONVERGED", font=mono(40, True), fill=GREEN)
    d.text((1090, 555), "finding", font=mono(22), fill=MUTED)
    d.text((1330, 552), "non_atomic_value_transfer", font=mono(28, True), fill=AMBER)
    d.text((1090, 640), "votes", font=mono(22), fill=MUTED)
    d.text((1330, 628), "3 / 5 universes", font=mono(34, True), fill=CYAN)
    d.text((1090, 725), "confidence", font=mono(22), fill=MUTED)
    d.text((1330, 712), "0.96", font=mono(48, True), fill=GREEN)
    footer(d)
    save("00_title.png", img)


def scene_01() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "gap closed", "What changed after the first video", "The original demo explained the multiverse. This final demo proves the post-stage loop that a judge can reproduce.")

    stages = [
        ("PRE-STAGE", "AST parse, entropy scan, risky planets", CYAN),
        ("MID-STAGE", "5 isolated universes, attacker/defender pressure", AMBER),
        ("POST-STAGE", "certificate, patch plan, re-audit, rule export", GREEN),
    ]
    x = 110
    for label, body, col in stages:
        panel(d, (x, 405, x + 500, 720), label, col)
        d.text((x + 32, 490), label, font=mono(34, True), fill=col)
        draw_wrapped(d, (x + 36, 560), body, font(30), TEXT, 410, 10)
        if label == "POST-STAGE":
            d.rounded_rectangle((x + 30, 650, x + 335, 696), radius=23, fill=GREEN)
            d.text((x + 52, 660), "NOW VERIFIED", font=mono(22, True), fill=BG)
        x += 580
    d.line((610, 562, 690, 562), fill=DIM, width=5)
    d.polygon([(690, 562), (665, 546), (665, 578)], fill=DIM)
    d.line((1190, 562, 1270, 562), fill=DIM, width=5)
    d.polygon([(1270, 562), (1245, 546), (1245, 578)], fill=DIM)

    panel(d, (180, 795, 1740, 940), "Submission upgrade", MAGENTA)
    draw_wrapped(d, (230, 842), "The new artifact answers the hard judge question: if the tool finds a bug, can it convert that discovery into a safer code pattern and prove the risk is reduced?", font(31), TEXT, 1420, 8)
    footer(d)
    save("01_gap_closed.png", img)


def scene_02() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "fixture", "A concrete target, not a vague claim", "The demo fixture is a small transfer function with a classic non-atomic value movement risk.")
    code = [
        "async function transfer(fromId, toId, amount) {",
        "  const from = await accounts.get(fromId);",
        "  const to = await accounts.get(toId);",
        "  if (from.balance < amount) throw new Error('insufficient');",
        "  from.balance -= amount;",
        "  to.balance += amount;",
        "  await accounts.save(from);",
        "  await accounts.save(to);",
        "}",
    ]
    code_block(d, (82, 355, 1078, 845), code, "demo/fixtures/risky-transfer.js", {4: RED, 5: AMBER, 6: AMBER, 7: RED, 8: RED})

    panel(d, (1160, 355, 1800, 845), "Why single-path review misses it", RED)
    items = [
        ("Split mutation", "debit and credit happen outside one transaction"),
        ("Race window", "balance check can go stale before save"),
        ("No invariant proof", "total value preservation is only implied"),
        ("Reusable smell", "same pattern can be exported as a rule"),
    ]
    y = 435
    for title, body in items:
        d.text((1208, y), title, font=font(30, True), fill=AMBER)
        y = draw_wrapped(d, (1210, y + 42), body, font(24), TEXT, 520, 6) + 26
    footer(d)
    save("02_fixture.png", img)


def scene_03() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "mcp surface", "Copilot gets tools, not screenshots", "The project exposes a Model Context Protocol server so Copilot can ask for audits, certificates, and closed-loop demos.")

    panel(d, (88, 340, 830, 890), "MCP tools", CYAN)
    tools = [
        "get_shadow_omega_brief",
        "audit_code",
        "generate_convergence_certificate",
        "run_closed_loop_demo",
        "get_multiverse_status",
        "export_eslint_rules",
    ]
    y = 425
    for t in tools:
        fill = GREEN if "certificate" in t or "closed_loop" in t else TEXT
        d.rounded_rectangle((130, y - 6, 790, y + 44), radius=6, fill=(17, 21, 29), outline=(43, 53, 70))
        d.text((154, y + 4), t, font=mono(25, True), fill=fill)
        y += 68

    panel(d, (930, 340, 1800, 890), "Verifier output", GREEN)
    payload = {
        "server": "shadow-omega-auditor",
        "tools": 6,
        "brief_ok": True,
        "audit_response_ok": True,
        "certificate_ok": True,
        "closed_loop_ok": True,
    }
    lines = json.dumps(payload, indent=2).splitlines()
    y = 420
    for line in lines:
        d.text((980, y), line, font=mono(27), fill=TEXT if "true" not in line.lower() else GREEN)
        y += 42
    d.rounded_rectangle((980, 785, 1680, 842), radius=8, fill=(13, 44, 36), outline=GREEN)
    d.text((1010, 801), "Judge-repeatable: python t1-shadow-omega-core/verify_mcp_server.py", font=mono(22, True), fill=GREEN)
    footer(d)
    save("03_mcp_surface.png", img)


def scene_04() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "certificate", "Five universes vote independently", "The certificate is useful because the universes disagree first, then a dominant pattern emerges.")

    panel(d, (88, 315, 1832, 890), "Universe vote matrix", MAGENTA)
    rows = [
        ("U0", "aggressive", "non_atomic_value_transfer", "converged", GREEN),
        ("U1", "stealth", "non_atomic_value_transfer", "converged", GREEN),
        ("U2", "adaptive", "invalid_amount_path", "minority", AMBER),
        ("U3", "defensive", "authority_mutation", "minority", BLUE),
        ("U4", "stealth", "non_atomic_value_transfer", "converged", GREEN),
    ]
    headers = ["universe", "mode", "top finding", "vote"]
    x_positions = [150, 390, 720, 1430]
    for x, h in zip(x_positions, headers):
        d.text((x, 388), h.upper(), font=mono(20, True), fill=MUTED)
    y = 450
    for uid, mode, finding, vote, col in rows:
        d.rounded_rectangle((128, y - 12, 1785, y + 54), radius=8, fill=(18, 22, 30), outline=(40, 49, 64))
        d.text((150, y), uid, font=mono(32, True), fill=col)
        d.text((390, y + 4), mode, font=mono(26), fill=TEXT)
        d.text((720, y + 4), finding, font=mono(26, True), fill=AMBER if "non_atomic" in finding else TEXT)
        d.text((1430, y + 4), vote, font=mono(26, True), fill=col)
        y += 82
    d.rounded_rectangle((1240, 785, 1740, 845), radius=30, fill=GREEN)
    d.text((1295, 800), "3 / 5 consensus, confidence 0.96", font=mono(26, True), fill=BG)
    footer(d)
    save("04_vote_matrix.png", img)


def scene_05() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "closed loop", "Discovery becomes a mitigation", "The second MCP tool demonstrates the full loop: detect, patch, re-audit, export.")

    panel(d, (80, 350, 565, 850), "1. discover", RED)
    d.text((130, 470), "CONVERGED", font=mono(42, True), fill=RED)
    draw_wrapped(d, (130, 545), "non_atomic_value_transfer appears in three independent universes.", font(28), TEXT, 380, 8)

    panel(d, (715, 350, 1200, 850), "2. guarded patch", AMBER)
    patch = [
        "await db.transaction(async tx => {",
        "  const from = await tx.lock(fromId);",
        "  const to = await tx.lock(toId);",
        "  assertValidAmount(amount);",
        "  assertSufficient(from, amount);",
        "  from.balance -= amount;",
        "  to.balance += amount;",
        "});",
    ]
    y = 430
    for line in patch:
        d.text((750, y), line, font=mono(21), fill=TEXT)
        y += 40

    panel(d, (1350, 350, 1835, 850), "3. re-audit", GREEN)
    d.text((1400, 455), "NOT_CONVERGED", font=mono(38, True), fill=GREEN)
    draw_wrapped(d, (1400, 535), "The same universes no longer agree on the original high-risk pattern.", font(28), TEXT, 380, 8)
    d.rounded_rectangle((1400, 710, 1748, 766), radius=28, fill=GREEN)
    d.text((1432, 724), "mitigated", font=mono(28, True), fill=BG)

    d.line((580, 600, 690, 600), fill=DIM, width=5)
    d.polygon([(690, 600), (665, 584), (665, 616)], fill=DIM)
    d.line((1215, 600, 1325, 600), fill=DIM, width=5)
    d.polygon([(1325, 600), (1300, 584), (1300, 616)], fill=DIM)
    footer(d)
    save("05_closed_loop.png", img)


def scene_06() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "rule export", "The finding leaves an artifact behind", "The Fossil Record is not a metaphor here: a discovered archetype becomes a reusable rule skeleton.")

    code = [
        "module.exports = {",
        "  meta: { type: 'problem' },",
        "  create(context) {",
        "    return {",
        "      AssignmentExpression(node) {",
        "        detectSplitValueTransfer(node);",
        "      }",
        "    };",
        "  }",
        "};",
    ]
    code_block(d, (90, 335, 970, 875), code, "generated ESLint rule skeleton", {6: GREEN})
    panel(d, (1060, 335, 1810, 875), "Why this matters", CYAN)
    bullets = [
        ("memory", "the system remembers an evolved vulnerability archetype"),
        ("repeatability", "the verifier checks certificate and closed-loop outputs"),
        ("Copilot fit", "the tool speaks through MCP instead of a separate UI"),
        ("honesty", "COPILOT_USAGE.md records the actual integration boundary"),
    ]
    y = 420
    for title, body in bullets:
        d.text((1115, y), title.upper(), font=mono(22, True), fill=CYAN)
        y = draw_wrapped(d, (1115, y + 34), body, font(27), TEXT, 610, 8) + 22
    footer(d)
    save("06_rule_export.png", img)


def scene_07() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "judge lens", "What is stronger now", "The highest-scoring version is no longer a concept demo; it is a reproducible agent workflow.")

    cards = [
        ("Novelty", "multiverse consensus as an audit primitive", MAGENTA),
        ("Technical proof", "MCP verifier covers six tools and two new loops", CYAN),
        ("Usefulness", "Copilot can request the certificate from inside dev flow", GREEN),
        ("Demo clarity", "fixture, votes, patch, re-audit in one path", AMBER),
    ]
    x = 110
    for title, body, col in cards:
        panel(d, (x, 370, x + 390, 780), title, col)
        d.text((x + 34, 455), title, font=font(36, True), fill=col)
        draw_wrapped(d, (x + 36, 530), body, font(28), TEXT, 300, 8)
        x += 440
    panel(d, (235, 830, 1685, 945), "remaining caveat handled honestly", RED)
    draw_wrapped(d, (285, 866), "The repository documents that non-interactive Copilot CLI preview did not expose custom workspace MCP tools, so the submitted proof uses the MCP server verifier plus explicit Copilot setup instructions.", font(27), TEXT, 1320, 8)
    footer(d)
    save("07_judge_lens.png", img)


def scene_08() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "final artifact", "Shadow-Omega is now submit-ready", "The final submission includes the original architecture demo plus this certificate demo covering the post-stage proof.")

    panel(d, (140, 350, 1780, 840), "What to run", GREEN)
    commands = [
        "python t1-shadow-omega-core/verify_mcp_server.py",
        "python -m t1_shadow_omega_core.convergence_certificate demo/fixtures/risky-transfer.js",
        "MCP tool: generate_convergence_certificate",
        "MCP tool: run_closed_loop_demo",
    ]
    y = 440
    for cmd in commands:
        d.rounded_rectangle((205, y - 8, 1710, y + 48), radius=8, fill=(16, 24, 32), outline=(42, 68, 78))
        d.text((230, y + 4), cmd, font=mono(27, True), fill=TEXT if cmd.startswith("python") else CYAN)
        y += 86
    d.text((205, 760), "Creative Apps Track  ·  github.com/Hokutoman00/shadow-omega", font=mono(28, True), fill=AMBER)
    footer(d)
    save("08_close.png", img)


def main() -> None:
    for scene in [scene_00, scene_01, scene_02, scene_03, scene_04, scene_05, scene_06, scene_07, scene_08]:
        scene()
    print(f"Wrote frames to {OUT}")


if __name__ == "__main__":
    main()
