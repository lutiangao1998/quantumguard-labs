"""
QuantumGuard Labs - Demo Chart Generator
=========================================
Generates visual assets for the GitHub README and documentation,
showing the output of the Quantum Risk Analysis engine.
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

# ── Color palette ──────────────────────────────────────────────────────────────
COLORS = {
    "bg":       "#0D1117",
    "bg2":      "#161B22",
    "border":   "#30363D",
    "text":     "#E6EDF3",
    "subtext":  "#8B949E",
    "critical": "#FF4444",
    "high":     "#FF8C00",
    "medium":   "#FFD700",
    "low":      "#3FB950",
    "safe":     "#58A6FF",
    "accent":   "#58A6FF",
    "green":    "#3FB950",
    "purple":   "#BC8CFF",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def set_dark_style():
    plt.rcParams.update({
        "figure.facecolor":  COLORS["bg"],
        "axes.facecolor":    COLORS["bg2"],
        "axes.edgecolor":    COLORS["border"],
        "axes.labelcolor":   COLORS["text"],
        "xtick.color":       COLORS["subtext"],
        "ytick.color":       COLORS["subtext"],
        "text.color":        COLORS["text"],
        "grid.color":        COLORS["border"],
        "grid.linewidth":    0.6,
        "font.family":       "DejaVu Sans",
        "font.size":         11,
    })


# ── Chart 1: Portfolio Risk Dashboard ─────────────────────────────────────────
def generate_risk_dashboard():
    set_dark_style()
    fig = plt.figure(figsize=(14, 8), facecolor=COLORS["bg"])
    fig.suptitle(
        "QuantumGuard Labs  |  Portfolio Quantum Risk Dashboard",
        fontsize=16, fontweight="bold", color=COLORS["text"], y=0.97
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38,
                           left=0.07, right=0.97, top=0.90, bottom=0.08)

    # ── Donut chart: risk distribution ────────────────────────────────────────
    ax_donut = fig.add_subplot(gs[0, 0])
    sizes   = [14, 37, 0, 149, 0]
    labels  = ["CRITICAL\n14", "HIGH\n37", "MEDIUM\n0", "LOW\n149", "SAFE\n0"]
    colors  = [COLORS["critical"], COLORS["high"], COLORS["medium"],
               COLORS["low"], COLORS["safe"]]
    wedge_colors = [c for c, s in zip(colors, sizes) if s > 0]
    wedge_sizes  = [s for s in sizes if s > 0]
    wedge_labels = [l for l, s in zip(labels, sizes) if s > 0]

    wedges, texts = ax_donut.pie(
        wedge_sizes, labels=None, colors=wedge_colors,
        startangle=90, wedgeprops=dict(width=0.52, edgecolor=COLORS["bg"], linewidth=2),
        pctdistance=0.82
    )
    ax_donut.text(0, 0, "200\nUTXOs", ha="center", va="center",
                  fontsize=13, fontweight="bold", color=COLORS["text"])
    ax_donut.set_title("UTXO Risk Distribution", color=COLORS["text"],
                       fontsize=11, pad=8)
    legend_patches = [mpatches.Patch(color=c, label=l)
                      for c, l in zip(wedge_colors, wedge_labels)]
    ax_donut.legend(handles=legend_patches, loc="lower center",
                    bbox_to_anchor=(0.5, -0.22), ncol=2,
                    fontsize=8, frameon=False, labelcolor=COLORS["text"])

    # ── Gauge: Quantum Readiness Score ────────────────────────────────────────
    ax_gauge = fig.add_subplot(gs[0, 1])
    ax_gauge.set_xlim(0, 10); ax_gauge.set_ylim(0, 6)
    ax_gauge.axis("off")
    ax_gauge.set_title("Quantum Readiness Score", color=COLORS["text"],
                       fontsize=11, pad=8)
    score = 61.2
    theta = np.linspace(np.pi, 0, 200)
    r = 2.5
    cx, cy = 5, 1.8
    for i, (t1, t2) in enumerate(zip(theta[:-1], theta[1:])):
        frac = i / len(theta)
        if frac < 0.25:   c = COLORS["critical"]
        elif frac < 0.50: c = COLORS["high"]
        elif frac < 0.75: c = COLORS["medium"]
        else:             c = COLORS["green"]
        ax_gauge.plot([cx + r*np.cos(t1), cx + r*np.cos(t2)],
                      [cy + r*np.sin(t1), cy + r*np.sin(t2)],
                      color=c, linewidth=10, solid_capstyle="round")
    needle_angle = np.pi - (score / 100) * np.pi
    ax_gauge.annotate("", xy=(cx + 2.0*np.cos(needle_angle), cy + 2.0*np.sin(needle_angle)),
                      xytext=(cx, cy),
                      arrowprops=dict(arrowstyle="-|>", color=COLORS["text"],
                                      lw=2.5, mutation_scale=18))
    ax_gauge.text(cx, cy + 0.5, f"{score}", ha="center", va="center",
                  fontsize=26, fontweight="bold", color=COLORS["text"])
    ax_gauge.text(cx, cy - 0.5, "/ 100", ha="center", va="center",
                  fontsize=12, color=COLORS["subtext"])
    ax_gauge.text(0.5, -0.05, "⚠  Action Required",
                  ha="center", va="center", fontsize=9,
                  color=COLORS["high"], transform=ax_gauge.transAxes)

    # ── Bar chart: BTC value at risk ───────────────────────────────────────────
    ax_btc = fig.add_subplot(gs[0, 2])
    risk_cats = ["CRITICAL", "HIGH", "LOW"]
    btc_vals  = [11.24, 32.51, 127.80]
    bar_cols  = [COLORS["critical"], COLORS["high"], COLORS["low"]]
    bars = ax_btc.barh(risk_cats, btc_vals, color=bar_cols,
                       edgecolor=COLORS["border"], height=0.55)
    for bar, val in zip(bars, btc_vals):
        ax_btc.text(val + 1.5, bar.get_y() + bar.get_height()/2,
                    f"{val:.2f} BTC", va="center", fontsize=9,
                    color=COLORS["text"])
    ax_btc.set_xlabel("BTC Value", color=COLORS["subtext"], fontsize=9)
    ax_btc.set_title("Value at Risk by Level", color=COLORS["text"],
                     fontsize=11, pad=8)
    ax_btc.set_xlim(0, 175)
    ax_btc.grid(axis="x", alpha=0.4)

    # ── Timeline: migration plan batches ──────────────────────────────────────
    ax_timeline = fig.add_subplot(gs[1, :2])
    batches = [
        ("Batch 1", "CRITICAL (14 UTXOs)", 14, 11.24, COLORS["critical"]),
        ("Batch 2", "HIGH — Part A (20 UTXOs)", 20, 17.30, COLORS["high"]),
        ("Batch 3", "HIGH — Part B (17 UTXOs)", 17, 15.21, COLORS["high"]),
    ]
    y_positions = [2, 1, 0]
    ax_timeline.set_xlim(0, 10); ax_timeline.set_ylim(-0.6, 2.8)
    ax_timeline.axis("off")
    ax_timeline.set_title("Migration Plan — Batch Schedule", color=COLORS["text"],
                           fontsize=11, pad=8)
    for (name, label, count, btc, col), y in zip(batches, y_positions):
        rect = mpatches.FancyBboxPatch((0.2, y - 0.35), 9.5, 0.70,
                                       boxstyle="round,pad=0.05",
                                       facecolor=col + "22", edgecolor=col, linewidth=1.5)
        ax_timeline.add_patch(rect)
        ax_timeline.text(0.5, y, f"▶  {name}", va="center", fontsize=10,
                         fontweight="bold", color=col)
        ax_timeline.text(3.2, y, label, va="center", fontsize=9,
                         color=COLORS["text"])
        ax_timeline.text(7.5, y + 0.18, f"{count} UTXOs", va="center",
                         fontsize=8, color=COLORS["subtext"])
        ax_timeline.text(7.5, y - 0.18, f"{btc:.2f} BTC", va="center",
                         fontsize=8, color=COLORS["subtext"])
        status = "PENDING APPROVAL" if y > 0 else "PENDING APPROVAL"
        ax_timeline.text(9.5, y, status, va="center", ha="right",
                         fontsize=7.5, color=COLORS["medium"],
                         bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["medium"]+"22",
                                   edgecolor=COLORS["medium"], linewidth=0.8))

    # ── Stats panel ───────────────────────────────────────────────────────────
    ax_stats = fig.add_subplot(gs[1, 2])
    ax_stats.axis("off")
    ax_stats.set_title("Migration Summary", color=COLORS["text"],
                        fontsize=11, pad=8)
    stats = [
        ("Total UTXOs Analyzed", "200"),
        ("UTXOs Requiring Migration", "51  (25.5%)"),
        ("Total BTC to Migrate", "43.75 BTC"),
        ("Estimated Tx Fees", "0.00076 BTC"),
        ("Migration Batches", "3"),
        ("Projected New Score", "96.2 / 100"),
    ]
    for i, (label, value) in enumerate(stats):
        y_pos = 0.88 - i * 0.155
        ax_stats.text(0.02, y_pos, label, transform=ax_stats.transAxes,
                      fontsize=8.5, color=COLORS["subtext"], va="top")
        ax_stats.text(0.98, y_pos - 0.05, value, transform=ax_stats.transAxes,
                      fontsize=10, fontweight="bold", color=COLORS["text"],
                      va="top", ha="right")
        if i < len(stats) - 1:
            line_y = y_pos - 0.12
            ax_stats.plot([0.02, 0.98], [line_y, line_y],
                          color=COLORS["border"], linewidth=0.5,
                          transform=ax_stats.transAxes)

    out_path = os.path.join(OUTPUT_DIR, "risk_dashboard.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLORS["bg"], edgecolor="none")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ── Chart 2: Architecture Diagram ─────────────────────────────────────────────
def generate_architecture_diagram():
    set_dark_style()
    fig, ax = plt.subplots(figsize=(13, 7), facecolor=COLORS["bg"])
    ax.set_xlim(0, 13); ax.set_ylim(0, 7)
    ax.axis("off")
    fig.suptitle("QuantumGuard Labs  |  System Architecture",
                 fontsize=15, fontweight="bold", color=COLORS["text"], y=0.97)

    def draw_box(ax, x, y, w, h, title, subtitle, color, icon=""):
        rect = mpatches.FancyBboxPatch((x, y), w, h,
                                       boxstyle="round,pad=0.12",
                                       facecolor=color + "1A",
                                       edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.28, f"{icon}  {title}",
                ha="center", va="top", fontsize=10, fontweight="bold", color=color)
        ax.text(x + w/2, y + h/2 - 0.1, subtitle,
                ha="center", va="center", fontsize=8, color=COLORS["subtext"],
                wrap=True, multialignment="center")

    def draw_arrow(ax, x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=COLORS["border"],
                                   lw=1.8, mutation_scale=14))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.12, label, ha="center", fontsize=7.5,
                    color=COLORS["subtext"])

    # Layer labels
    for y_pos, label in [(5.6, "INPUT LAYER"), (3.9, "ANALYSIS LAYER"),
                          (2.2, "EXECUTION LAYER"), (0.5, "OUTPUT LAYER")]:
        ax.text(0.15, y_pos, label, fontsize=7, color=COLORS["subtext"],
                rotation=90, va="center")

    # Input layer
    draw_box(ax, 1.0, 5.1, 2.5, 1.1, "Bitcoin Node", "UTXO Set / RPC", COLORS["accent"], "⛓")
    draw_box(ax, 4.5, 5.1, 2.5, 1.1, "Institution", "Custody System / HSM", COLORS["purple"], "🏦")
    draw_box(ax, 8.0, 5.1, 2.5, 1.1, "Policy Config", "Risk Thresholds / Rules", COLORS["medium"], "⚙")

    # Analysis layer
    draw_box(ax, 1.0, 3.4, 3.5, 1.1, "Risk Analyzer", "UTXO Scan · Script Classification\nRisk Scoring · Readiness Score", COLORS["critical"], "🔍")
    draw_box(ax, 5.5, 3.4, 3.5, 1.1, "Crypto-Agility Layer", "ECDSA · ML-DSA-44 (Dilithium)\nHybrid Signature Support", COLORS["safe"], "🔐")

    # Execution layer
    draw_box(ax, 1.0, 1.7, 3.5, 1.1, "Migration Orchestrator", "Batch Planning · Priority Queue\nApproval Workflow · Tx Builder", COLORS["high"], "🚀")
    draw_box(ax, 5.5, 1.7, 3.5, 1.1, "Audit & Proof Engine", "Hash-Chain Log · Readiness Proof\nCompliance Report Generation", COLORS["green"], "📋")

    # Output layer
    draw_box(ax, 1.0, 0.2, 2.2, 1.0, "Risk Report", "JSON / Markdown", COLORS["critical"], "📊")
    draw_box(ax, 3.8, 0.2, 2.2, 1.0, "Migration Plan", "Batches / Txns", COLORS["high"], "📝")
    draw_box(ax, 6.6, 0.2, 2.2, 1.0, "Readiness Proof", "Audit Trail / PDF", COLORS["green"], "✅")
    draw_box(ax, 9.4, 0.2, 2.2, 1.0, "Signed Txns", "Broadcast to Chain", COLORS["safe"], "📡")

    # Arrows
    draw_arrow(ax, 2.25, 5.1, 2.25, 4.5, "UTXO data")
    draw_arrow(ax, 5.75, 5.1, 5.75, 4.5, "Sign request")
    draw_arrow(ax, 4.5, 3.95, 5.5, 3.95, "Risk list")
    draw_arrow(ax, 2.75, 3.4, 2.75, 2.8, "Eligible UTXOs")
    draw_arrow(ax, 7.25, 3.4, 7.25, 2.8, "Signed txns")
    draw_arrow(ax, 4.5, 2.25, 5.5, 2.25, "Audit events")
    draw_arrow(ax, 2.1, 1.7, 2.1, 1.2)
    draw_arrow(ax, 4.5, 1.7, 4.9, 1.2)
    draw_arrow(ax, 6.5, 1.7, 7.7, 1.2)
    draw_arrow(ax, 9.0, 1.7, 10.5, 1.2)

    out_path = os.path.join(OUTPUT_DIR, "architecture_diagram.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLORS["bg"], edgecolor="none")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ── Chart 3: Risk Score Timeline ──────────────────────────────────────────────
def generate_score_timeline():
    set_dark_style()
    fig, ax = plt.subplots(figsize=(11, 4.5), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg2"])

    months = ["Month 1\n(Baseline)", "Month 2\n(Batch 1)", "Month 3\n(Batch 2)",
              "Month 4\n(Batch 3)", "Month 5\n(Verification)", "Month 6\n(Complete)"]
    scores = [61.2, 68.5, 78.3, 88.1, 93.7, 96.2]
    x = np.arange(len(months))

    ax.fill_between(x, scores, alpha=0.15, color=COLORS["accent"])
    ax.plot(x, scores, color=COLORS["accent"], linewidth=2.5,
            marker="o", markersize=9, markerfacecolor=COLORS["bg"],
            markeredgecolor=COLORS["accent"], markeredgewidth=2.5, zorder=5)

    for xi, score in zip(x, scores):
        color = COLORS["critical"] if score < 70 else \
                COLORS["high"] if score < 80 else \
                COLORS["medium"] if score < 90 else COLORS["green"]
        ax.text(xi, score + 2.5, f"{score}", ha="center", fontsize=10,
                fontweight="bold", color=color)

    ax.axhline(y=90, color=COLORS["green"], linestyle="--", linewidth=1.2, alpha=0.7)
    ax.text(5.1, 90.5, "Target ≥ 90", fontsize=8.5, color=COLORS["green"], alpha=0.9)
    ax.axhspan(0, 70, alpha=0.06, color=COLORS["critical"])
    ax.axhspan(70, 90, alpha=0.04, color=COLORS["medium"])
    ax.axhspan(90, 105, alpha=0.04, color=COLORS["green"])

    ax.set_xticks(x); ax.set_xticklabels(months, fontsize=9)
    ax.set_ylabel("Quantum Readiness Score", fontsize=10)
    ax.set_ylim(50, 105); ax.set_xlim(-0.3, 5.3)
    ax.set_title("Quantum Readiness Score — 6-Month Migration Roadmap",
                 fontsize=13, fontweight="bold", color=COLORS["text"], pad=12)
    ax.grid(axis="y", alpha=0.4)

    out_path = os.path.join(OUTPUT_DIR, "score_timeline.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLORS["bg"], edgecolor="none")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    print("\nGenerating QuantumGuard Labs demo charts...")
    generate_risk_dashboard()
    generate_architecture_diagram()
    generate_score_timeline()
    print("\nAll charts generated successfully.\n")
