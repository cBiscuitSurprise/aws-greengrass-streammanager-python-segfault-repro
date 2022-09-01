import click

from utils import execute_command, update_config_version


def build(version: str):
    command = ["gdk", "component", "build"]

    update_config_version(version)

    print(f"building component version: {version}")
    for line in execute_command(command):
        print(line.decode())

    print("... done")


@click.command()
@click.option("--version", type=str, help="The new version to deploy")
def _build(version: str):
    build(version)


if __name__ == "__main__":
    _build()
