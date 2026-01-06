"""CLI utilities for running pytopoviz workflows.

Author: B.G.
"""

from __future__ import annotations

from typing import Dict, Optional

import click

from .workflow import Workflow


def _prompt_gui(specs: Dict[str, dict], provided: Dict[str, str], only_loaders: Optional[set[str]] = None) -> Dict[str, str]:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    resolved = dict(provided)
    prompt_specs: Dict[str, dict] = {}
    for name, spec in specs.items():
        if name in resolved:
            continue
        if only_loaders is not None and name not in only_loaders:
            if "default" in spec:
                resolved[name] = str(spec["default"])
            continue
        prompt_specs[name] = spec

    root = tk.Tk()
    root.title("pytopoviz workflow inputs")
    root.geometry("640x520")

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, borderwidth=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    form = tk.Frame(canvas)

    form.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=form, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    widgets: Dict[str, Dict[str, object]] = {}

    def browse_path(target_var: tk.StringVar) -> None:
        selected = filedialog.askopenfilename()
        if selected:
            target_var.set(selected)

    row = 0
    for name, spec in prompt_specs.items():
        input_type = spec.get("type", "str")
        prompt = spec.get("prompt", name)
        default = spec.get("default")

        label = tk.Label(form, text=prompt, anchor="w", justify="left", wraplength=420)
        label.grid(row=row, column=0, sticky="w", padx=8, pady=6)

        if input_type == "bool":
            var = tk.BooleanVar(value=bool(default) if default is not None else False)
            widget = tk.Checkbutton(form, variable=var)
            widget.grid(row=row, column=1, sticky="w", padx=8, pady=6)
            widgets[name] = {"type": "bool", "var": var}
        else:
            var = tk.StringVar(value=str(default) if default is not None else "")
            entry = tk.Entry(form, textvariable=var, width=40)
            entry.grid(row=row, column=1, sticky="w", padx=8, pady=6)
            widgets[name] = {"type": input_type, "var": var}
            if input_type == "path":
                button = tk.Button(form, text="Browse", command=lambda v=var: browse_path(v))
                button.grid(row=row, column=2, sticky="w", padx=8, pady=6)
        row += 1

    result: Dict[str, str] = {}

    def submit() -> None:
        missing = []
        for name, info in widgets.items():
            input_type = info["type"]
            var = info["var"]
            if input_type == "bool":
                result[name] = str(bool(var.get()))
                continue
            value = str(var.get()).strip()
            if value == "":
                missing.append(name)
                continue
            result[name] = value
        if missing:
            messagebox.showerror("Missing input", f"Missing required values for: {', '.join(missing)}.")
            return
        root.quit()

    def cancel() -> None:
        root.destroy()
        raise click.ClickException("Input cancelled.")

    controls = tk.Frame(root)
    controls.pack(fill="x")
    tk.Button(controls, text="Cancel", command=cancel).pack(side="right", padx=8, pady=8)
    tk.Button(controls, text="Run", command=submit).pack(side="right", padx=8, pady=8)

    root.mainloop()
    root.destroy()

    resolved.update(result)
    return resolved


def _prompt_cli(specs: Dict[str, dict], provided: Dict[str, str], only_loaders: Optional[set[str]] = None) -> Dict[str, str]:
    resolved = dict(provided)
    for name, spec in specs.items():
        if name in resolved:
            continue
        if only_loaders is not None and name not in only_loaders:
            if "default" in spec:
                resolved[name] = str(spec["default"])
            continue
        prompt = spec.get("prompt", name)
        default = spec.get("default")
        resolved[name] = click.prompt(prompt, default=default, show_default=default is not None)
    return resolved


def _parse_param_file(path: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                raise click.ClickException(f"Invalid param line '{line.strip()}'. Use key=value.")
            key, val = stripped.split("=", 1)
            values[key.strip()] = val.strip()
    return values


def _write_param_file(path: str, specs: Dict[str, dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# pytopoviz workflow parameters\n")
        for name, spec in specs.items():
            default = spec.get("default", "")
            handle.write(f"{name}={default}\n")


def _loader_inputs(workflow: Workflow) -> set[str]:
    refs: set[str] = set()
    for data_spec in workflow.spec.get("data_sources", {}).values():
        params = data_spec.get("params", {})
        stack = list(params.values())
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                if "$ref" in item:
                    refs.add(item["$ref"])
                else:
                    stack.extend(item.values())
            elif isinstance(item, (list, tuple)):
                stack.extend(item)
    return refs


@click.command()
@click.argument("workflow_path", type=click.Path(exists=True))
@click.option("--gui", "ui_mode", flag_value="gui", default="cli", help="Interactive GUI prompts.")
@click.option("--cli", "ui_mode", flag_value="cli", help="Interactive CLI prompts (default).")
@click.option("--file", "param_file", required=False, default=None, flag_value="__GENERATE__", help="Read inputs from a param file, or generate one when used without a path.")
@click.option("--mode", type=click.Choice(["fig2d", "fig3d", "both"]), default=None)
@click.option("--fast", is_flag=True, default=False, help="Prompt only loader inputs, use defaults for others.")
def main(workflow_path: str, ui_mode: str, param_file: Optional[str], mode: Optional[str], fast: bool):
    """Run a workflow from a JSON file."""
    workflow = Workflow.from_file(workflow_path)
    workflow.validate_defaults()

    if param_file == "__GENERATE__":
        output_path = f"{workflow_path}.params"
        _write_param_file(output_path, workflow.input_specs())
        click.echo(f"Wrote default params to {output_path}")
        return

    if param_file:
        provided = _parse_param_file(param_file)
    else:
        loader_inputs = _loader_inputs(workflow) if fast else None
        if ui_mode == "gui":
            provided = _prompt_gui(workflow.input_specs(), {}, only_loaders=loader_inputs)
        else:
            provided = _prompt_cli(workflow.input_specs(), {}, only_loaders=loader_inputs)

    inputs = workflow.resolve_inputs(provided)
    workflow.run(inputs, mode=mode)
