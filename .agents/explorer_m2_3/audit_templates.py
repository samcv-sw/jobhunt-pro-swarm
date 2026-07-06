import os
import ast
import jinja2
from jinja2 import meta

TEMPLATE_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
APP_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"
OUTPUT_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3\audit_output.txt"

def get_template_variables():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    template_vars = {}
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if not file.endswith(".html"):
                continue
            rel_path = os.path.relpath(os.path.join(root, file), TEMPLATE_DIR).replace("\\", "/")
            try:
                source = env.loader.get_source(env, rel_path)[0]
                ast_tree = env.parse(source)
                vars_in_tmpl = meta.find_undeclared_variables(ast_tree)
                template_vars[rel_path] = sorted(list(vars_in_tmpl))
            except Exception as e:
                template_vars[rel_path] = f"ERROR: {e}"
    return template_vars

class RenderTemplateVisitor(ast.NodeVisitor):
    def __init__(self):
        self.renders = []
        self.dashboard_shell_renders = []
        self.public_shell_renders = []

    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in ("render_template", "_build_dashboard_shell", "_public_shell"):
            args = []
            kwargs = {}
            for arg in node.args:
                if isinstance(arg, ast.Constant):
                    args.append(arg.value)
                else:
                    args.append(f"expr:{ast.unparse(arg)}")
            for kw in node.keywords:
                val = ast.unparse(kw.value) if kw.value else "None"
                kwargs[kw.arg] = val
            
            call_info = {
                "func": func_name,
                "line": node.lineno,
                "args": args,
                "kwargs": kwargs
            }
            if func_name == "render_template":
                self.renders.append(call_info)
            elif func_name == "_build_dashboard_shell":
                self.dashboard_shell_renders.append(call_info)
            elif func_name == "_public_shell":
                self.public_shell_renders.append(call_info)

        self.generic_visit(node)

def analyze_app_renders():
    with open(APP_FILE, "r", encoding="utf-8") as f:
        code = f.read()
    tree = ast.parse(code)
    visitor = RenderTemplateVisitor()
    visitor.visit(tree)
    return visitor.renders, visitor.dashboard_shell_renders, visitor.public_shell_renders

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("--- Extracting template undeclared variables ---\n")
        tmpl_vars = get_template_variables()
        for name, vars_list in sorted(tmpl_vars.items()):
            out.write(f"{name}: {vars_list}\n")

        out.write("\n--- Extracting backend render calls ---\n")
        renders, dash_renders, pub_renders = analyze_app_renders()
        
        out.write("\n--- render_template Calls ---\n")
        for r in renders:
            out.write(f"Line {r['line']}: render_template({', '.join(repr(a) for a in r['args'])}, {', '.join(f'{k}={v}' for k, v in r['kwargs'].items())})\n")

        out.write("\n--- _build_dashboard_shell Calls ---\n")
        for r in dash_renders:
            out.write(f"Line {r['line']}: _build_dashboard_shell({', '.join(repr(a) for a in r['args'])}, {', '.join(f'{k}={v}' for k, v in r['kwargs'].items())})\n")

        out.write("\n--- _public_shell Calls ---\n")
        for r in pub_renders:
            out.write(f"Line {r['line']}: _public_shell({', '.join(repr(a) for a in r['args'])}, {', '.join(f'{k}={v}' for k, v in r['kwargs'].items())})\n")

if __name__ == "__main__":
    main()
