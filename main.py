"""
main.py - GUI Application for CFG Derivation Tree and AST Generator.
Course: ST0244 - Programming Languages and Computing Paradigms
EAFIT University - Lecturer: Alexander Narváez Berrío
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import io

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from grammar import Grammar, Derivation
from tree_visualizer import TreeVisualizer


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & DEFAULT GRAMMAR
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_GRAMMAR = """\
# Arithmetic expression grammar
E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | num | id
"""

DEFAULT_EXPRESSION = "num + num * num"

DARK = {
    'bg':          '#0d1117',
    'surface':     '#161b22',
    'surface2':    '#21262d',
    'border':      '#30363d',
    'accent':      '#58a6ff',
    'accent2':     '#3fb950',
    'accent3':     '#f78166',
    'text':        '#e6edf3',
    'text_muted':  '#8b949e',
    'success':     '#238636',
    'error':       '#da3633',
    'warning':     '#9e6a03',
}

FONT_MONO = ('Courier New', 10)
FONT_MONO_SM = ('Courier New', 9)
FONT_UI = ('Segoe UI', 10)
FONT_TITLE = ('Segoe UI', 13, 'bold')
FONT_HEADER = ('Segoe UI', 11, 'bold')


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION CLASS
# ─────────────────────────────────────────────────────────────────────────────

class CFGApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("CFG Parser — Derivation Tree & AST Generator")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(bg=DARK['bg'])

        self.grammar = Grammar()
        self.derivation = None
        self.visualizer = TreeVisualizer()

        self._build_ui()
        self._load_default_grammar()

    # ── UI CONSTRUCTION ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        self._build_topbar()

        # Main paned layout: left panel | right notebook
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=DARK['border'], sashwidth=4,
                               sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        left = self._build_left_panel(paned)
        right = self._build_right_panel(paned)

        paned.add(left, minsize=320)
        paned.add(right, minsize=600)
        paned.paneconfigure(left, width=380)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=DARK['surface'], height=52)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        tk.Label(bar, text="⟨/⟩", font=('Courier New', 20, 'bold'),
                 fg=DARK['accent'], bg=DARK['surface']).pack(side=tk.LEFT, padx=(16, 6), pady=8)

        tk.Label(bar, text="CFG Parser", font=FONT_TITLE,
                 fg=DARK['text'], bg=DARK['surface']).pack(side=tk.LEFT, pady=8)

        tk.Label(bar, text="Derivation Tree & AST Generator",
                 font=('Segoe UI', 10), fg=DARK['text_muted'],
                 bg=DARK['surface']).pack(side=tk.LEFT, padx=(8, 0), pady=8)

        tk.Label(bar, text="ST0244 · EAFIT", font=('Segoe UI', 9),
                 fg=DARK['text_muted'], bg=DARK['surface']).pack(side=tk.RIGHT, padx=16)

    def _build_left_panel(self, parent):
        frame = tk.Frame(parent, bg=DARK['bg'])

        # ── Grammar section ──────────────────────────────────────────────────
        self._section_label(frame, "Grammar Definition (BNF)")

        self.grammar_text = scrolledtext.ScrolledText(
            frame, height=12, font=FONT_MONO_SM,
            bg=DARK['surface2'], fg='#79c0ff',
            insertbackground=DARK['accent'],
            relief=tk.FLAT, borderwidth=0,
            selectbackground=DARK['accent'],
            highlightthickness=1,
            highlightbackground=DARK['border'],
            wrap=tk.NONE
        )
        self.grammar_text.pack(fill=tk.X, padx=10, pady=(0, 4))

        btn_row = tk.Frame(frame, bg=DARK['bg'])
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        self._btn(btn_row, "✓ Validate Grammar", self._validate_grammar,
                  DARK['success']).pack(side=tk.LEFT)
        self._btn(btn_row, "↺ Reset", self._load_default_grammar,
                  DARK['surface2']).pack(side=tk.LEFT, padx=(6, 0))

        self.grammar_status = tk.Label(frame, text="", font=('Segoe UI', 9),
                                        bg=DARK['bg'], fg=DARK['text_muted'])
        self.grammar_status.pack(anchor='w', padx=12)

        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=8)

        # ── Expression section ───────────────────────────────────────────────
        self._section_label(frame, "Target Expression")

        expr_frame = tk.Frame(frame, bg=DARK['bg'])
        expr_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.expr_var = tk.StringVar(value=DEFAULT_EXPRESSION)
        expr_entry = tk.Entry(expr_frame, textvariable=self.expr_var,
                              font=FONT_MONO, bg=DARK['surface2'],
                              fg=DARK['accent2'], insertbackground='white',
                              relief=tk.FLAT, highlightthickness=1,
                              highlightbackground=DARK['border'])
        expr_entry.pack(fill=tk.X)

        tk.Label(frame, text="Separate tokens with spaces  (e.g.: num + num * num)",
                 font=('Segoe UI', 8), fg=DARK['text_muted'],
                 bg=DARK['bg']).pack(anchor='w', padx=12)

        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=8)

        # ── Derivation options ───────────────────────────────────────────────
        self._section_label(frame, "Derivation Options")

        self.direction_var = tk.StringVar(value='left')

        opt_frame = tk.Frame(frame, bg=DARK['surface'], relief=tk.FLAT,
                              highlightthickness=1, highlightbackground=DARK['border'])
        opt_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        for val, label in [('left', '⟵  Left Derivation'), ('right', '⟶  Right Derivation')]:
            rb = tk.Radiobutton(opt_frame, text=label, variable=self.direction_var,
                                value=val, font=FONT_UI,
                                bg=DARK['surface'], fg=DARK['text'],
                                selectcolor=DARK['surface2'],
                                activebackground=DARK['surface'],
                                activeforeground=DARK['accent'])
            rb.pack(anchor='w', padx=12, pady=4)

        generate_btn = tk.Button(frame, text="▶  Generate Derivation",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=DARK['accent'], fg='white',
                                  relief=tk.FLAT, cursor='hand2',
                                  activebackground='#388bfd',
                                  command=self._run_derivation,
                                  pady=8)
        generate_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=4)

        # ── Grammar info ─────────────────────────────────────────────────────
        self._section_label(frame, "Grammar Info")
        self.info_text = scrolledtext.ScrolledText(
            frame, height=8, font=FONT_MONO_SM,
            bg=DARK['surface2'], fg=DARK['text_muted'],
            relief=tk.FLAT, borderwidth=0,
            highlightthickness=1, highlightbackground=DARK['border'],
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        return frame

    def _build_right_panel(self, parent):
        frame = tk.Frame(parent, bg=DARK['bg'])

        # Status bar
        self.status_bar = tk.Label(frame, text="Ready. Define a grammar and enter an expression.",
                                    font=('Segoe UI', 9), fg=DARK['text_muted'],
                                    bg=DARK['surface'], anchor='w', padx=12, pady=5)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Notebook tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TNotebook', background=DARK['bg'], borderwidth=0)
        style.configure('Dark.TNotebook.Tab',
                         background=DARK['surface2'], foreground=DARK['text_muted'],
                         padding=[14, 6], font=('Segoe UI', 10))
        style.map('Dark.TNotebook.Tab',
                  background=[('selected', DARK['surface'])],
                  foreground=[('selected', DARK['accent'])])

        nb = ttk.Notebook(frame, style='Dark.TNotebook')
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Derivation steps
        self.deriv_frame = tk.Frame(nb, bg=DARK['bg'])
        nb.add(self.deriv_frame, text='  📋 Derivation Steps  ')
        self._build_derivation_tab(self.deriv_frame)

        # Tab 2: Derivation tree
        self.dtree_frame = tk.Frame(nb, bg=DARK['bg'])
        nb.add(self.dtree_frame, text='  🌳 Derivation Tree  ')
        self._build_tree_tab(self.dtree_frame, 'deriv')

        # Tab 3: AST
        self.ast_frame = tk.Frame(nb, bg=DARK['bg'])
        nb.add(self.ast_frame, text='  ✦ Abstract Syntax Tree  ')
        self._build_tree_tab(self.ast_frame, 'ast')

        return frame

    def _build_derivation_tab(self, parent):
        header = tk.Frame(parent, bg=DARK['surface'])
        header.pack(fill=tk.X)
        tk.Label(header, text="Step-by-step derivation of the expression",
                 font=('Segoe UI', 10), fg=DARK['text_muted'],
                 bg=DARK['surface'], pady=6, padx=12).pack(side=tk.LEFT)

        self.deriv_text = scrolledtext.ScrolledText(
            parent, font=('Courier New', 12),
            bg=DARK['surface2'], fg='#c9d1d9',
            insertbackground='white', relief=tk.FLAT,
            highlightthickness=1, highlightbackground=DARK['border'],
            state=tk.DISABLED, padx=16, pady=12
        )
        self.deriv_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Configure tags
        self.deriv_text.tag_configure('step_num', foreground=DARK['text_muted'],
                                       font=('Courier New', 11))
        self.deriv_text.tag_configure('arrow', foreground=DARK['accent'],
                                       font=('Courier New', 12, 'bold'))
        self.deriv_text.tag_configure('terminal', foreground=DARK['accent2'],
                                       font=('Courier New', 12, 'bold'))
        self.deriv_text.tag_configure('non_terminal', foreground='#79c0ff',
                                       font=('Courier New', 12))
        self.deriv_text.tag_configure('rule_label', foreground=DARK['accent3'],
                                       font=('Courier New', 10))
        self.deriv_text.tag_configure('header', foreground=DARK['accent'],
                                       font=('Courier New', 12, 'bold'))

    def _build_tree_tab(self, parent, tag):
        # Toolbar
        toolbar = tk.Frame(parent, bg=DARK['surface'])
        toolbar.pack(fill=tk.X)

        self._btn(toolbar, "🔍 Zoom In",
                  lambda: self._zoom(tag, 1.2), DARK['surface2']).pack(side=tk.LEFT, padx=4, pady=4)
        self._btn(toolbar, "🔎 Zoom Out",
                  lambda: self._zoom(tag, 0.8), DARK['surface2']).pack(side=tk.LEFT, padx=(0, 4), pady=4)
        self._btn(toolbar, "⤡ Fit",
                  lambda: self._fit(tag), DARK['surface2']).pack(side=tk.LEFT, padx=(0, 4), pady=4)
        self._btn(toolbar, "💾 Save PNG",
                  lambda: self._save_tree(tag), DARK['accent']).pack(side=tk.RIGHT, padx=4, pady=4)

        # Canvas placeholder
        canvas_frame = tk.Frame(parent, bg=DARK['surface2'],
                                 highlightthickness=1, highlightbackground=DARK['border'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        placeholder = tk.Label(canvas_frame,
                                text="Generate a derivation to see the tree here.",
                                font=('Segoe UI', 12), fg=DARK['text_muted'],
                                bg=DARK['surface2'])
        placeholder.pack(expand=True)

        if tag == 'deriv':
            self.dtree_canvas_frame = canvas_frame
            self.dtree_placeholder = placeholder
            self.dtree_fig_canvas = None
            self.dtree_fig = None
        else:
            self.ast_canvas_frame = canvas_frame
            self.ast_placeholder = placeholder
            self.ast_fig_canvas = None
            self.ast_fig = None

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _section_label(self, parent, text: str):
        tk.Label(parent, text=text.upper(), font=('Segoe UI', 8, 'bold'),
                 fg=DARK['text_muted'], bg=DARK['bg'],
                 pady=4).pack(anchor='w', padx=12)

    def _btn(self, parent, text: str, cmd, color: str) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         font=('Segoe UI', 9), bg=color, fg=DARK['text'],
                         relief=tk.FLAT, cursor='hand2',
                         activebackground=DARK['border'],
                         padx=10, pady=4)

    def _set_status(self, msg: str, color: str = None):
        self.status_bar.config(text=f"  {msg}", fg=color or DARK['text_muted'])

    def _set_text(self, widget, content: str):
        widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, content)
        widget.config(state=tk.DISABLED)

    # ── LOGIC CALLBACKS ───────────────────────────────────────────────────────

    def _load_default_grammar(self):
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', DEFAULT_GRAMMAR.strip())
        self.expr_var.set(DEFAULT_EXPRESSION)
        self._validate_grammar()

    def _validate_grammar(self):
        text = self.grammar_text.get('1.0', tk.END)
        self.grammar.parse_from_text(text)
        valid, msg = self.grammar.is_valid()

        if valid:
            self.grammar_status.config(
                text=f"✓ Valid · {len(self.grammar.productions)} productions · "
                     f"Start: {self.grammar.start_symbol}",
                fg=DARK['accent2'])
            self._update_grammar_info()
            self._set_status("Grammar validated successfully.", DARK['accent2'])
        else:
            self.grammar_status.config(text=f"✗ {msg}", fg=DARK['error'])
            self._set_status(f"Grammar error: {msg}", DARK['error'])

    def _update_grammar_info(self):
        g = self.grammar
        lines = [
            f"Start symbol : {g.start_symbol}",
            f"Non-terminals: {', '.join(sorted(g.non_terminals))}",
            f"Terminals    : {', '.join(sorted(g.terminals))}",
            f"Productions  : {len(g.productions)}",
            "",
            "── Productions ──────────────────",
        ]
        for p in g.productions:
            lines.append(f"  {p}")

        self._set_text(self.info_text, '\n'.join(lines))

    def _run_derivation(self):
        valid, msg = self.grammar.is_valid()
        if not valid:
            messagebox.showerror("Grammar Error", f"Invalid grammar:\n{msg}")
            return

        expr = self.expr_var.get().strip()
        if not expr:
            messagebox.showwarning("Input Error", "Please enter a target expression.")
            return

        tokens = expr.split()
        direction = self.direction_var.get()
        self._set_status("⏳ Computing derivation…", DARK['warning'])
        self.update()

        # Run in thread to keep UI responsive
        threading.Thread(target=self._compute, args=(tokens, direction), daemon=True).start()

    def _compute(self, tokens: list, direction: str):
        deriv = Derivation(self.grammar)
        found = deriv.derive(tokens, direction=direction, max_steps=500)

        # Update UI from main thread
        self.after(0, lambda: self._show_results(deriv, found, tokens, direction))

    def _show_results(self, deriv: Derivation, found: bool, tokens: list, direction: str):
        if not found:
            self._set_status(
                f"✗ Could not derive '{' '.join(tokens)}' with {direction} derivation. "
                "Check grammar and expression.", DARK['error'])
            messagebox.showerror("Derivation Failed",
                                  f"The expression  '{' '.join(tokens)}'  could not be derived "
                                  f"from the grammar using {direction} derivation.\n\n"
                                  "Tips:\n• Check that all tokens are defined as terminals\n"
                                  "• Check production rules\n• Try the other direction")
            return

        self.derivation = deriv
        self._show_derivation_steps(deriv, direction)
        self._show_tree(deriv.derivation_tree, 'deriv',
                        f"Derivation Tree  ({direction} derivation)  →  {' '.join(tokens)}")
        self._show_tree(deriv.ast, 'ast',
                        f"Abstract Syntax Tree  →  {' '.join(tokens)}")

        n = len(deriv.steps) - 1
        self._set_status(
            f"✓ Derived in {n} step{'s' if n != 1 else ''}  ({direction} derivation)", DARK['accent2'])

    def _show_derivation_steps(self, deriv: Derivation, direction: str):
        w = self.deriv_text
        w.config(state=tk.NORMAL)
        w.delete('1.0', tk.END)

        dir_label = "Left" if direction == 'left' else "Right"
        w.insert(tk.END, f"{'─'*60}\n", 'header')
        w.insert(tk.END, f"  {dir_label} Derivation  ·  {len(deriv.steps)-1} step(s)\n", 'header')
        w.insert(tk.END, f"{'─'*60}\n\n", 'header')

        for i, step in enumerate(deriv.steps):
            # Step number
            w.insert(tk.END, f"[{i:>3}] ", 'step_num')

            # Arrow
            if i > 0:
                w.insert(tk.END, "⟹  ", 'arrow')
            else:
                w.insert(tk.END, "    ", 'step_num')

            # Sentential form — color terminals vs non-terminals
            for j, sym in enumerate(step.sentential_form):
                if self.grammar.is_terminal(sym):
                    w.insert(tk.END, sym, 'terminal')
                else:
                    w.insert(tk.END, sym, 'non_terminal')
                if j < len(step.sentential_form) - 1:
                    w.insert(tk.END, ' ')

            # Rule applied
            if step.rule_applied:
                w.insert(tk.END, f"      [{step.rule_applied}]", 'rule_label')

            w.insert(tk.END, '\n')

        w.insert(tk.END, f"\n{'─'*60}\n", 'header')
        w.insert(tk.END, f"  Result: {' '.join(deriv.steps[-1].sentential_form)}\n", 'terminal')
        w.config(state=tk.DISABLED)

    def _show_tree(self, root, tag: str, title: str):
        if root is None:
            return

        theme = (self.visualizer.DERIVATION_THEME if tag == 'deriv'
                 else self.visualizer.AST_THEME)

        # Count leaves to estimate width
        leaves = self._count_leaves(root)
        w = max(10, min(leaves * 1.4, 22))
        h = max(6, min(self._tree_depth(root) * 1.5, 12))

        fig = self.visualizer.draw(root, title=title, theme=theme, figsize=(w, h))

        if tag == 'deriv':
            frame = self.dtree_canvas_frame
            placeholder = self.dtree_placeholder
            if self.dtree_fig_canvas:
                self.dtree_fig_canvas.get_tk_widget().destroy()
                plt.close(self.dtree_fig)
        else:
            frame = self.ast_canvas_frame
            placeholder = self.ast_placeholder
            if self.ast_fig_canvas:
                self.ast_fig_canvas.get_tk_widget().destroy()
                plt.close(self.ast_fig)

        placeholder.pack_forget()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        if tag == 'deriv':
            self.dtree_fig_canvas = canvas
            self.dtree_fig = fig
        else:
            self.ast_fig_canvas = canvas
            self.ast_fig = fig

    def _count_leaves(self, node) -> int:
        if not node:
            return 0
        if not node.children:
            return 1
        return sum(self._count_leaves(c) for c in node.children)

    def _tree_depth(self, node, d=0) -> int:
        if not node or not node.children:
            return d
        return max(self._tree_depth(c, d+1) for c in node.children)

    def _zoom(self, tag: str, factor: float):
        pass  # Matplotlib zoom handled natively

    def _fit(self, tag: str):
        pass

    def _save_tree(self, tag: str):
        from tkinter.filedialog import asksaveasfilename
        fig = self.dtree_fig if tag == 'deriv' else self.ast_fig
        if fig is None:
            messagebox.showinfo("Nothing to save", "Generate a derivation first.")
            return
        path = asksaveasfilename(defaultextension='.png',
                                  filetypes=[('PNG Image', '*.png'), ('All files', '*.*')],
                                  title='Save tree as…')
        if path:
            fig.savefig(path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            self._set_status(f"✓ Saved to {path}", DARK['accent2'])


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = CFGApp()
    app.mainloop()
