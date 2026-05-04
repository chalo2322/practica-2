"""
tree_visualizer.py - Renders derivation trees and ASTs using matplotlib.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from grammar import TreeNode


class TreeLayout:
    """Computes (x, y) positions for tree nodes using Reingold-Tilford inspired algorithm."""

    def __init__(self):
        self.positions = {}
        self.x_counter = [0]

    def compute(self, root: TreeNode, depth: int = 0) -> dict:
        self.positions = {}
        self.x_counter = [0]
        self._assign_positions(root, depth=0)
        return self.positions

    def _assign_positions(self, node: TreeNode, depth: int):
        if not node.children:
            x = self.x_counter[0]
            self.x_counter[0] += 1
            self.positions[id(node)] = (x, -depth)
            return x

        child_xs = []
        for child in node.children:
            cx = self._assign_positions(child, depth + 1)
            child_xs.append(cx)

        x = (child_xs[0] + child_xs[-1]) / 2.0
        self.positions[id(node)] = (x, -depth)
        return x


class TreeVisualizer:
    """Draws a tree on a matplotlib figure."""

    # Color themes
    DERIVATION_THEME = {
        'bg': '#0f0f1a',
        'nt_fill': '#1e3a5f',
        'nt_edge': '#4a9eff',
        'nt_text': '#e8f4fd',
        'term_fill': '#1a3a1a',
        'term_edge': '#4aff7a',
        'term_text': '#c8ffd4',
        'edge_color': '#334466',
        'title_color': '#4a9eff',
    }

    AST_THEME = {
        'bg': '#1a0f0f',
        'nt_fill': '#3d1a00',
        'nt_edge': '#ff6b35',
        'nt_text': '#ffe8d6',
        'term_fill': '#1a1a00',
        'term_edge': '#ffd700',
        'term_text': '#fff9c4',
        'edge_color': '#664433',
        'title_color': '#ff6b35',
    }

    def draw(self, root: TreeNode, title: str = "Tree", theme: dict = None, figsize=(12, 8)) -> plt.Figure:
        if theme is None:
            theme = self.DERIVATION_THEME

        layout = TreeLayout()
        positions = layout.compute(root)

        if not positions:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No tree to display", ha='center', va='center',
                    color='white', fontsize=14)
            ax.set_facecolor(theme['bg'])
            fig.patch.set_facecolor(theme['bg'])
            return fig

        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(theme['bg'])
        ax.set_facecolor(theme['bg'])

        # Draw edges first
        self._draw_edges(ax, root, positions, theme)

        # Draw nodes
        self._draw_nodes(ax, root, positions, theme)

        # Styling
        margin_x = max(1.0, (x_max - x_min) * 0.1)
        margin_y = max(0.5, (y_max - y_min) * 0.15)
        ax.set_xlim(x_min - margin_x, x_max + margin_x)
        ax.set_ylim(y_min - margin_y, y_max + margin_y)
        ax.axis('off')

        ax.set_title(title, color=theme['title_color'], fontsize=15,
                     fontweight='bold', pad=12, fontfamily='monospace')

        # Legend
        nt_patch = mpatches.Patch(facecolor=theme['nt_fill'], edgecolor=theme['nt_edge'],
                                   label='Non-terminal', linewidth=1.5)
        t_patch = mpatches.Patch(facecolor=theme['term_fill'], edgecolor=theme['term_edge'],
                                  label='Terminal', linewidth=1.5)
        ax.legend(handles=[nt_patch, t_patch], loc='lower right',
                  facecolor=theme['bg'], edgecolor=theme['nt_edge'],
                  labelcolor='white', fontsize=8)

        plt.tight_layout()
        return fig

    def _draw_edges(self, ax, node: TreeNode, positions: dict, theme: dict):
        if id(node) not in positions:
            return
        x1, y1 = positions[id(node)]
        for child in node.children:
            if id(child) in positions:
                x2, y2 = positions[id(child)]
                ax.plot([x1, x2], [y1, y2], color=theme['edge_color'],
                        linewidth=1.5, zorder=1, alpha=0.8)
            self._draw_edges(ax, child, positions, theme)

    def _draw_nodes(self, ax, node: TreeNode, positions: dict, theme: dict):
        if id(node) not in positions:
            return
        x, y = positions[id(node)]

        if node.is_terminal:
            fill = theme['term_fill']
            edge = theme['term_edge']
            text_color = theme['term_text']
            shape = 'round,pad=0.3'
        else:
            fill = theme['nt_fill']
            edge = theme['nt_edge']
            text_color = theme['nt_text']
            shape = 'round,pad=0.3'

        bbox = dict(boxstyle=shape, facecolor=fill, edgecolor=edge,
                    linewidth=2.0, zorder=2)
        ax.text(x, y, node.label, ha='center', va='center',
                fontsize=10, fontweight='bold', color=text_color,
                bbox=bbox, zorder=3, fontfamily='monospace')

        for child in node.children:
            self._draw_nodes(ax, child, positions, theme)


def fig_to_image(fig: plt.Figure):
    """Convert matplotlib figure to PIL Image for Tkinter display."""
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf)
    return img
