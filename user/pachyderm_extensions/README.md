# JupyterLab Pachyderm Extensions

JupyterLab extensions for Pachyderm.

This extension is composed of a Python package named `pachyderm_extensions`
for the server extension and a NPM package named `jupyterlab_pachyderm_extensions`
for the frontend extension.

## Requirements

- JupyterLab >= 2.0

## Install

Note: You will need NodeJS to installed the extension.

```bash
pip install .
jupyter lab build
```

## Troubleshoot

If you are see the frontend extension but it is not working, check
that the server extension is enabled:

```bash
jupyter serverextension list
```

If the server extension is installed and enabled but your not seeing
the frontend, check the frontend is installed:

```bash
jupyter labextension list
```

If it is installed, try:

```bash
jupyter lab clean
jupyter lab build
```

## Contributing

### Development Install

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to pachyderm_extensions directory
# Install server extension
pip install -e .
# Register server extension
jupyter serverextension enable --py pachyderm_extensions
# Install dependencies
jlpm
# Build Typescript source
jlpm build
# Link your development version of the extension with JupyterLab
jupyter labextension link .

# Rebuild Typescript source after making changes
jlpm build
# Rebuild JupyterLab after making any changes
jupyter lab build
```

You can watch the source directory and run JupyterLab in watch mode to watch for changes in the extension's source and automatically rebuild the extension and application.

```bash
# Watch the source directory in another terminal tab
jlpm watch
# Run jupyterlab in watch mode in one terminal tab
jupyter lab --watch
```

### Uninstall

```bash
pip uninstall pachyderm_extensions
jupyter labextension uninstall jupyterlab_pachyderm_extensions
```
