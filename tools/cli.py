#!/usr/bin/env python3
"""
CLI tool for JHipster.github.io-jp development and translation management.
"""

import click
import sys
import os

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config  # noqa: E402
from git_utils import git_utils  # noqa: E402


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """JHipster.github.io-jp development and translation tools."""
    if verbose:
        click.echo("Verbose mode enabled")


@cli.command()
def status():
    """Show repository and configuration status."""
    click.echo("JHipster.github.io-jp Tools Status")
    click.echo("=" * 35)

    # Repository info
    if git_utils.is_repository():
        click.echo(f"Repository: {git_utils.get_repository_root()}")
        click.echo(f"Current branch: {git_utils.get_current_branch()}")
        click.echo(f"Has uncommitted changes: {git_utils.has_uncommitted_changes()}")
    else:
        click.echo("Error: Not in a git repository")

    # Configuration info
    click.echo(f"Source language: {config.get('source_lang')}")
    click.echo(f"Target language: {config.get('target_lang')}")
    click.echo(f"Docs directory: {config.get('docs_dir')}")


@cli.command()
def translate():
    """Translation management commands."""
    click.echo("Translation functionality - To be implemented")


@cli.command()
def sync():
    """Synchronize translations with source documents."""
    click.echo("Sync functionality - To be implemented")


@cli.command()
def validate():
    """Validate translations and documentation."""
    click.echo("Validation functionality - To be implemented")


if __name__ == "__main__":
    cli()
