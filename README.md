# SPST AutoFlow Controller

## Installation and Uninstallation

Install AutoFlow in editable mode:
1. Open `Command Prompt` or `Anaconda Prompt`
2. cd to `\python-package`, where `pyproject.toml` is located
3. Run `pip install -e .` (Note: there is a DOT at the end)

Uninstall AutoFlow:
1. Open `Command Prompt` or `Anaconda Prompt`
2. Run `pip uninstall autoflow`

## Add extraPahts to enable Pylance extension in VS Code
The Pylance extension will fail to recognize the package install with `pip install -e .`.
To sovle this problem, add the path where the parent directory of `autoflow` to `.vscode/settings.json`, e.g.,
> "python.analysis.extraPaths": ["D:/GitLab/spst-autoflow/"]
