"""
grammar.py - Core OOP classes for CFG parsing, derivation, and AST generation.
Uses Earley parsing to correctly handle left-recursive grammars.
"""


class Symbol:
    """Represents a grammar symbol (terminal or non-terminal)."""

    def __init__(self, name: str, is_terminal: bool):
        self.name = name
        self.is_terminal = is_terminal

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Production:
    """Represents a production rule: head -> body."""

    def __init__(self, head: str, body: list):
        self.head = head
        self.body = body

    def __repr__(self):
        return f"{self.head} -> {' '.join(self.body)}"


class Grammar:
    """Context-Free Grammar."""

    def __init__(self):
        self.productions: list = []
        self.non_terminals: set = set()
        self.terminals: set = set()
        self.start_symbol: str = None

    def parse_from_text(self, text: str):
        self.productions.clear()
        self.non_terminals.clear()
        self.terminals.clear()
        self.start_symbol = None

        lines = [l.strip() for l in text.strip().splitlines()
                 if l.strip() and not l.strip().startswith('#')]

        for line in lines:
            sep = None
            if '->' in line:
                sep = '->'
            elif '::=' in line:
                sep = '::='
            if sep is None:
                continue

            parts = line.split(sep, 1)
            if len(parts) != 2:
                continue

            head = parts[0].strip()
            rhs = parts[1].strip()

            self.non_terminals.add(head)
            if self.start_symbol is None:
                self.start_symbol = head

            for alt in [a.strip() for a in rhs.split('|')]:
                body = alt.split()
                if body:
                    self.productions.append(Production(head, body))

        all_syms = set()
        for p in self.productions:
            for s in p.body:
                all_syms.add(s)
        self.terminals = all_syms - self.non_terminals

    def get_productions_for(self, nt: str) -> list:
        return [p for p in self.productions if p.head == nt]

    def is_terminal(self, sym: str) -> bool:
        return sym not in self.non_terminals

    def is_valid(self) -> tuple:
        if not self.productions:
            return False, "No productions defined."
        if not self.start_symbol:
            return False, "No start symbol found."
        return True, ""


class DerivationStep:
    """One step in a derivation sequence."""

    def __init__(self, sentential_form: list, rule_applied=None, expanded_index: int = -1):
        self.sentential_form = sentential_form[:]
        self.rule_applied = rule_applied
        self.expanded_index = expanded_index

    def __repr__(self):
        return ' '.join(self.sentential_form)


class TreeNode:
    """Node in a derivation tree or AST."""

    def __init__(self, label: str, is_terminal: bool = False):
        self.label = label
        self.is_terminal = is_terminal
        self.children: list = []

    def add_child(self, node):
        self.children.append(node)

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __repr__(self):
        return f"TreeNode({self.label})"


class Derivation:
    """
    Earley parser + derivation step extractor + AST builder.
    Handles left-recursive and right-recursive CFGs correctly.
    """

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.steps: list = []
        self.derivation_tree: TreeNode = None
        self.ast: TreeNode = None

    def derive(self, target_tokens: list, direction: str = 'left',
               max_steps: int = 300) -> bool:
        self.steps = []
        self.derivation_tree = None
        self.ast = None

        tree = self._earley_parse(target_tokens)
        if tree is None:
            return False

        self.derivation_tree = tree
        self.steps = self._extract_steps(tree, direction)
        self.ast = self._build_ast(tree)
        return True

    def get_steps_text(self) -> list:
        lines = []
        for i, step in enumerate(self.steps):
            arrow = "⟹" if i > 0 else " "
            lines.append(f"{arrow} {' '.join(step.sentential_form)}")
        return lines

    # ─── EARLEY PARSER ────────────────────────────────────────────────────────

    def _earley_parse(self, tokens: list):
        """
        Earley parser. Returns a TreeNode (parse tree) or None.
        Each chart item: (head, body_tuple, dot, origin, children_list)
        """
        n = len(tokens)
        chart = [[] for _ in range(n + 1)]
        item_keys = [set() for _ in range(n + 1)]

        def add(k, head, body, dot, origin, children):
            key = (head, body, dot, origin)
            if key not in item_keys[k]:
                item_keys[k].add(key)
                chart[k].append([head, body, dot, origin, children])

        # Seed
        for prod in self.grammar.get_productions_for(self.grammar.start_symbol):
            add(0, prod.head, tuple(prod.body), 0, 0, [])

        for k in range(n + 1):
            i = 0
            while i < len(chart[k]):
                head, body, dot, origin, children = chart[k][i]
                i += 1

                if dot == len(body):
                    # Completion — find items waiting for `head` starting at `origin`
                    for item in list(chart[origin]):
                        h2, b2, d2, o2, ch2 = item
                        if d2 < len(b2) and b2[d2] == head:
                            node = TreeNode(head, is_terminal=False)
                            node.children = list(children)
                            add(k, h2, b2, d2 + 1, o2, list(ch2) + [node])
                else:
                    next_sym = body[dot]
                    if not self.grammar.is_terminal(next_sym):
                        # Prediction
                        for prod in self.grammar.get_productions_for(next_sym):
                            add(k, prod.head, tuple(prod.body), 0, k, [])
                    elif k < n and tokens[k] == next_sym:
                        # Scan
                        tnode = TreeNode(next_sym, is_terminal=True)
                        add(k + 1, head, body, dot + 1, origin, list(children) + [tnode])

        # Find completed start item spanning full input
        for item in chart[n]:
            head, body, dot, origin, children = item
            if head == self.grammar.start_symbol and dot == len(body) and origin == 0:
                root = TreeNode(self.grammar.start_symbol, is_terminal=False)
                root.children = list(children)
                return root

        return None

    # ─── STEP EXTRACTION ─────────────────────────────────────────────────────

    def _extract_steps(self, root: TreeNode, direction: str) -> list:
        steps = [DerivationStep([self.grammar.start_symbol])]
        expansions = []
        self._collect_expansions(root, expansions, direction)

        current = [self.grammar.start_symbol]
        for node in expansions:
            if node.is_terminal or not node.children:
                continue
            child_labels = [c.label for c in node.children]
            rule = Production(node.label, child_labels)

            if direction == 'left':
                idx = next((i for i, s in enumerate(current)
                            if s == node.label and not self.grammar.is_terminal(s)), -1)
            else:
                idx = next((i for i, s in reversed(list(enumerate(current)))
                            if s == node.label and not self.grammar.is_terminal(s)), -1)

            if idx == -1:
                continue

            current = current[:idx] + child_labels + current[idx + 1:]
            steps.append(DerivationStep(current, rule, idx))

        return steps

    def _collect_expansions(self, node: TreeNode, result: list, direction: str):
        if node.is_terminal or not node.children:
            return
        result.append(node)
        ordered = node.children if direction == 'left' else list(reversed(node.children))
        for child in ordered:
            self._collect_expansions(child, result, direction)

    # ─── AST ─────────────────────────────────────────────────────────────────

    def _build_ast(self, node: TreeNode):
        if node is None:
            return None
        if node.is_terminal:
            return TreeNode(node.label, is_terminal=True)

        ast_children = []
        for child in node.children:
            c = self._build_ast(child)
            if c is not None:
                ast_children.append(c)

        # Chain rule elimination
        if len(ast_children) == 1 and not ast_children[0].is_terminal:
            return ast_children[0]

        if not ast_children:
            return None

        new_node = TreeNode(node.label, is_terminal=False)
        new_node.children = ast_children
        return new_node
