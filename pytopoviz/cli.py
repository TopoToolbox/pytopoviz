"""CLI utilities for running pytopoviz workflows.

Author: B.G.
"""

from __future__ import annotations

from typing import Dict, Optional

import click

from .workflow import Workflow


def _prompt_gui(specs: Dict[str, dict], provided: Dict[str, str], only_loaders: Optional[set[str]] = None) -> Dict[str, str]:
    import tkinter as tk
    from tkinter import filedialog, simpledialog, messagebox

    resolved = dict(provided)
    root = tk.Tk()
    root.withdraw()

    for name, spec in specs.items():
        if name in resolved:
            continue
        if only_loaders is not None and name not in only_loaders:
            if "default" in spec:
                resolved[name] = str(spec["default"])
            continue
        input_type = spec.get("type", "str")
        prompt = spec.get("prompt", name)
        default = spec.get("default")

        if input_type == "path":
            path = filedialog.askopenfilename(title=prompt)
            if not path:
                messagebox.showerror("Missing input", f"Missing required path for '{name}'.")
                raise click.ClickException(f"Missing required path for '{name}'.")
            resolved[name] = path
            continue

        value = None
        while value is None:
            if input_type == "bool":
                value = messagebox.askyesno("Input", prompt)
            else:
                value = simpledialog.askstring("Input", f"{prompt}", initialvalue=str(default) if default is not None else "")
            if value is None:
                messagebox.showerror("Missing input", f"Missing required value for '{name}'.")
        resolved[name] = value

    root.destroy()
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
