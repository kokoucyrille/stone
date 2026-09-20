"""Figures Plotly au style de la maquette (fond transparent, sobres, lisibles)."""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go

from utils import config as C
from utils.formatting import fmt_int, fmt_pct
from utils.geo import load_regions_geojson

FONT = "Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Liberation Sans', sans-serif"
NAVY, SLATE, MUTED, GRID = (C.COLORS[k] for k in ("navy", "slate", "muted", "grid"))


def _layout(height: int, **extra) -> dict:
    base = dict(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=SLATE),
        separators=", ",  # virgule décimale, espace pour les milliers
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID,
                        font=dict(family=FONT, size=12, color=NAVY)),
        dragmode=False,
    )
    base.update(extra)
    return base


def _text_color(hex_color: str) -> str:
    """Blanc sur fond sombre, bleu nuit sur fond clair."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#FFFFFF" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else NAVY


def region_color(name: str, index: int = 0) -> str:
    return C.REGION_COLORS.get(name, C.FALLBACK_COLORS[index % len(C.FALLBACK_COLORS)])


PALETTE = C.SECTOR_COLORS + C.EXTRA_COLORS


def sector_colors(labels: list[str]) -> list[str]:
    colors, i = [], 0
    for label in labels:
        if label == "Autres":
            colors.append(C.OTHER_COLOR)
        else:
            colors.append(PALETTE[i % len(PALETTE)])
            i += 1
    return colors


# --------------------------------------------------------------------------- #
# Carte
# --------------------------------------------------------------------------- #
def _polygon_xy(geometry: dict) -> tuple[list, list]:
    """Contours (lon, lat) d'un Polygon/MultiPolygon, anneaux séparés par None."""
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    xs: list = []
    ys: list = []
    for polygon in polygons:
        for ring in polygon:
            xs += [pt[0] for pt in ring] + [None]
            ys += [pt[1] for pt in ring] + [None]
    return xs, ys


def region_map(regions: pd.DataFrame | None, height: int = 420, unit: str = "entreprises",
               value_format=fmt_int, highlight: str | None = None) -> go.Figure:
    """Carte des régions ; sans données, les polygones restent neutres.

    Le tracé utilise des polygones Scatter (et non `go.Choropleth`) : aucune
    ressource externe n'est téléchargée, la carte fonctionne hors connexion.
    """
    geo = load_regions_geojson()
    values = {} if regions is None or regions.empty else dict(zip(regions["label"], regions["valeur"]))
    parts = {} if regions is None or regions.empty or "part" not in regions else \
        dict(zip(regions["label"], regions["part"]))
    fig = go.Figure()
    polygon_names: set[str] = set()
    lons: list[float] = []
    lats: list[float] = []

    points = [C.GEO_POINTS[n] for n in values if n in C.GEO_POINTS]
    for i, feature in enumerate(geo["features"]):
        props = feature["properties"]
        name = props["region"]
        polygon_names.add(name)
        has = name in values
        selected = not values and highlight == name  # filtre actif, pas encore de données
        color = region_color(name, i) if (has or selected) else C.COLORS["empty"]
        hover = (f"<b>{name}</b><br>{value_format(values[name])} {unit}"
                 + (f" ({fmt_pct(parts[name])})" if name in parts else "")
                 if has else f"<b>{name}</b><br>"
                 + ("Région sélectionnée" if selected else "Donnée non disponible"))
        xs, ys = _polygon_xy(feature["geometry"])
        lons += [x for x in xs if x is not None]
        lats += [y for y in ys if y is not None]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself", fillcolor=color, name=name,
            line=dict(color="#FFFFFF", width=1.6), hoveron="fills", text=hover, hoverinfo="text",
            showlegend=False,
        ))
        label = f"{name}<br><b>{value_format(values[name])}</b>" if has else name
        # Remonte légèrement l'étiquette si une pastille (ex. Grand Lomé) la chevauche.
        near = any(abs(props["cy"] - lat) < 0.5 and abs(props["cx"] - lon) < 0.6 for lat, lon in points)
        fig.add_trace(go.Scatter(
            x=[props["cx"]], y=[props["cy"] + (0.2 if near else 0)], mode="text", text=[label],
            hoverinfo="skip",
            showlegend=False,
            textfont=dict(family=FONT, size=11,
                          color=_text_color(color) if (has or selected) else MUTED),
        ))

    # Régions localisables par un point (ex. Grand Lomé) absentes des polygones.
    extra = [(n, v) for n, v in values.items() if n not in polygon_names and n in C.GEO_POINTS]
    if extra:
        vmax = max(v for _, v in extra) or 1
        for i, (name, value) in enumerate(extra):
            lat, lon = C.GEO_POINTS[name]
            fig.add_trace(go.Scatter(
                x=[lon], y=[lat], mode="markers+text", showlegend=False,
                marker=dict(size=12 + 16 * math.sqrt(value / vmax), color=region_color(name, i),
                            line=dict(color="#FFFFFF", width=1.5)),
                text=[f"{name}<br><b>{value_format(value)}</b>"], textposition="bottom center",
                textfont=dict(family=FONT, size=11, color=NAVY),
                hovertemplate=f"<b>{name}</b><br>{value_format(value)} {unit}"
                              + (f" ({fmt_pct(parts[name])})" if name in parts else "")
                              + "<extra></extra>",
            ))

    x0, x1 = min(lons) - 0.55, max(lons) + 0.55
    y0, y1 = min(lats) - 0.7, max(lats) + 0.15
    fig.update_layout(**_layout(height, margin=dict(l=0, r=0, t=0, b=0), showlegend=False))
    fig.update_xaxes(visible=False, range=[x0, x1], constrain="domain", fixedrange=True)
    fig.update_yaxes(visible=False, range=[y0, y1], scaleanchor="x", scaleratio=1,
                     constrain="domain", fixedrange=True)
    return fig


# --------------------------------------------------------------------------- #
# Séries temporelles
# --------------------------------------------------------------------------- #
def evolution_chart(series: pd.Series, height: int = 230, name: str = "Entreprises") -> go.Figure:
    years = [int(y) for y in series.index]
    values = [float(v) for v in series.values]
    green = C.COLORS["green"]
    fig = go.Figure(go.Scatter(
        x=years, y=values, mode="lines+markers+text", name=name,
        line=dict(color="#0A8F5A", width=2.6),
        fill="tozeroy", fillcolor="rgba(14,159,110,0.12)",
        marker=dict(size=8, color="#FFFFFF", line=dict(color="#0A8F5A", width=2.2)),
        text=[fmt_int(v) for v in values], textposition="top center",
        textfont=dict(size=11, color=NAVY),
        hovertemplate="%{x} : <b>%{y:,.0f}</b><extra></extra>", cliponaxis=False,
    ))
    top = max(values) if values else 1
    fig.update_layout(**_layout(height, margin=dict(l=44, r=18, t=22, b=26), showlegend=False))
    fig.update_xaxes(tickmode="array", tickvals=years, showgrid=False, linecolor=GRID,
                     tickfont=dict(size=11, color=MUTED), fixedrange=True)
    fig.update_yaxes(range=[0, top * 1.22], gridcolor=GRID, zeroline=False, tickformat=",d",
                     tickfont=dict(size=11, color=MUTED), fixedrange=True, nticks=6)
    return fig


def multi_line(table: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = go.Figure()
    palette = PALETTE
    for i, column in enumerate(table.columns):
        fig.add_trace(go.Scatter(
            x=[int(y) for y in table.index], y=table[column], mode="lines+markers", name=str(column),
            line=dict(color=palette[i % len(palette)], width=2.2), marker=dict(size=6),
            hovertemplate="%{x} · " + str(column) + " : <b>%{y:,.0f}</b><extra></extra>",
        ))
    fig.update_layout(**_layout(height, margin=dict(l=44, r=10, t=10, b=30),
                                legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=11))))
    fig.update_xaxes(tickmode="array", tickvals=[int(y) for y in table.index], showgrid=False,
                     linecolor=GRID, fixedrange=True, tickfont=dict(size=11, color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickformat=",d", fixedrange=True,
                     tickfont=dict(size=11, color=MUTED))
    return fig


# --------------------------------------------------------------------------- #
# Répartitions
# --------------------------------------------------------------------------- #
def donut(df: pd.DataFrame, center_label: str = "entreprises", height: int = 210,
          colors: list[str] | None = None) -> go.Figure:
    colors = colors or sector_colors(list(df["label"]))
    total = df["valeur"].sum()
    fig = go.Figure(go.Pie(
        labels=df["label"], values=df["valeur"], hole=0.68, sort=False, direction="clockwise",
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)), textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} (%{percent:.1%})<extra></extra>",
        showlegend=False,
    ))
    fig.add_annotation(
        text=f"<b>{fmt_int(total)}</b><br><span style='font-size:12px;color:{SLATE}'>{center_label}</span>",
        showarrow=False, font=dict(size=22, color=NAVY, family=FONT),
    )
    fig.update_layout(**_layout(height, margin=dict(l=4, r=4, t=4, b=4)))
    return fig


def top_bars(df: pd.DataFrame, height: int = 170, colors: list[str] | None = None,
             value_format=fmt_int) -> go.Figure:
    """Barres horizontales sur une piste grise, valeur en bout de piste."""
    n = len(df)
    palette = colors or (C.BAR_GRADIENT if n <= len(C.BAR_GRADIENT) else
                         [C.BAR_GRADIENT[min(i * len(C.BAR_GRADIENT) // n, 4)] for i in range(n)])
    vmax = float(df["valeur"].max()) or 1.0
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df["label"], x=[vmax] * n, orientation="h",
                         marker=dict(color="#EEF2F6"), hoverinfo="skip", width=0.56))
    fig.add_trace(go.Bar(
        y=df["label"], x=df["valeur"], orientation="h", marker=dict(color=palette[:n]),
        width=0.56, hovertemplate="<b>%{y}</b> : %{x:,.0f}<extra></extra>",
    ))
    for label, value in zip(df["label"], df["valeur"]):
        fig.add_annotation(x=vmax * 1.03, y=label, text=value_format(value), showarrow=False,
                           xanchor="left", font=dict(size=11.5, color=NAVY))
    fig.update_layout(**_layout(height, barmode="overlay", showlegend=False,
                                margin=dict(l=4, r=44, t=2, b=2)))
    fig.update_xaxes(visible=False, range=[0, vmax * 1.16], fixedrange=True)
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11.5, color=NAVY),
                     fixedrange=True, automargin=True)
    return fig


def vertical_bars(df: pd.DataFrame, height: int = 190, colors: list[str] | None = None,
                  percent: bool = True) -> go.Figure:
    colors = colors or [region_color(l, i) for i, l in enumerate(df["label"])]
    texts = [fmt_pct(v, 0) if percent else fmt_int(v) for v in df["valeur"]]
    fig = go.Figure(go.Bar(
        x=df["label"], y=df["valeur"], marker=dict(color=colors), text=texts,
        textposition="outside", textfont=dict(size=11, color=NAVY), cliponaxis=False,
        hovertemplate="<b>%{x}</b> : %{y:,.1f}" + ("%" if percent else "") + "<extra></extra>",
        width=0.62,
    ))
    top = max(100.0, float(df["valeur"].max())) if percent else float(df["valeur"].max()) * 1.18
    fig.update_layout(**_layout(height, margin=dict(l=40, r=6, t=22, b=22), showlegend=False))
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(size=10, color=MUTED),
                     fixedrange=True, tickmode="array", tickvals=list(df["label"]),
                     ticktext=[str(l).replace(" ", "<br>") for l in df["label"]], tickangle=0)
    fig.update_yaxes(range=[0, top * (1.02 if percent else 1)], gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=10.5, color=MUTED), fixedrange=True,
                     ticksuffix="%" if percent else "", tickformat=",d", nticks=6)
    return fig


def stacked_bars(table: pd.DataFrame, height: int = 300) -> go.Figure:
    """`table` : index = catégories (axe X), colonnes = séries."""
    fig = go.Figure()
    palette = PALETTE
    for i, column in enumerate(table.columns):
        fig.add_trace(go.Bar(x=table.index, y=table[column], name=str(column),
                             marker=dict(color=palette[i % len(palette)]),
                             hovertemplate="<b>%{x}</b> · " + str(column) + " : %{y:,.0f}<extra></extra>"))
    fig.update_layout(**_layout(height, barmode="stack", margin=dict(l=44, r=10, t=10, b=30),
                                legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=11))))
    fig.update_xaxes(showgrid=False, linecolor=GRID, fixedrange=True, tickfont=dict(size=11, color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickformat=",d", fixedrange=True,
                     tickfont=dict(size=11, color=MUTED))
    return fig


def heatmap(table: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=table.values, x=[str(c) for c in table.columns], y=[str(i) for i in table.index],
        colorscale=[[0, "#F1F6F4"], [0.5, "#7CC29B"], [1, "#006A4E"]], showscale=False,
        xgap=2, ygap=2, hovertemplate="<b>%{y}</b> × %{x}<br>%{z:,.0f}<extra></extra>",
        text=[[fmt_int(v) if v else "" for v in row] for row in table.values],
        texttemplate="%{text}", textfont=dict(size=11),
    ))
    fig.update_layout(**_layout(height, margin=dict(l=8, r=8, t=8, b=8)))
    fig.update_xaxes(side="top", tickfont=dict(size=11, color=SLATE), fixedrange=True)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11, color=SLATE), fixedrange=True,
                     automargin=True)
    return fig
