# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Custom build script for GDK component build operation. This script is not designed to
be executed directly. It is designed to be used by GDK.

Example execution:
gdk component build
"""

import os
import shutil
from subprocess import PIPE, Popen
import sys
from typing import List
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


from GdkConfig import GdkConfig

DIRECTORY_STAGING_ASSETS = "greengrass-build/asset"
DIRECTORY_OUTPUT_ARTIFACTS = "greengrass-build/artifacts/"
FILE_RECIPE_TEMPLATE = "recipe.yaml"
FILE_RECIPE_OUTPUT = "greengrass-build/recipes/recipe.yaml"
FILE_ZIP_BASE = "package"
FILE_ZIP_EXT = "zip"


def create_recipe(config: GdkConfig):
    """Creates the component recipe, filling in the Docker images and Secret ARN"""
    print(f"creating recipe {FILE_RECIPE_OUTPUT} ...")

    with open(FILE_RECIPE_TEMPLATE, encoding="utf-8") as recipe_template_file:
        recipe_str = recipe_template_file.read()

    # TODO: do any replacements or other massaging to the recipe
    recipe_str = recipe_str.replace("{COMPONENT_NAME}", config.component_name)
    recipe_str = recipe_str.replace("{COMPONENT_VERSION}", config.component_version)
    recipe_str = recipe_str.replace("{COMPONENT_AUTHOR}", config.component_author)
    recipe_str = recipe_str.replace("{BUCKET_NAME}", config.publish_bucket)

    recipe = yaml.load(recipe_str, Loader=Loader)

    recipe_output_dir = os.path.dirname(FILE_RECIPE_OUTPUT)
    if not os.path.exists(recipe_output_dir):
        os.makedirs(recipe_output_dir)

    with open(FILE_RECIPE_OUTPUT, "w", encoding="utf-8") as recipe_file:
        yaml.dump(recipe, recipe_file, Dumper=Dumper)

    print("... recipe created")


def _do_command(command):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    stack = []
    while p.returncode is None or len(stack) != 0:
        if p.returncode is None:
            stack.append(p.stdout.read())
            stack.append(p.stderr.read())
            p.poll()

        yield stack.pop(0)

    if p.returncode != 0:
        raise RuntimeError(f"failed to execute command: `{' '.join(command)}`")


def _execute_command(command: List[str]):
    for line in _do_command(command):
        print(line.rstrip(b"\r\n"))
        sys.stdout.flush()


def do_build(name: str, version: str):
    print(f"building ...")
    dockerfile = "support/gdk_build.Dockerfile"
    image_tag = f"{name}:build".lower()
    temp_container = f"{name}-temporary"
    _execute_command(
        [
            "docker",
            "build",
            "-f",
            dockerfile,
            "-t",
            image_tag,
            ".",
        ]
    )
    print(f"extracting build files ...")
    if not os.path.exists(DIRECTORY_STAGING_ASSETS):
        print(f"creating staging directory: {DIRECTORY_STAGING_ASSETS}")
        os.makedirs(DIRECTORY_STAGING_ASSETS)

    _execute_command(["docker", "create", "--name", temp_container, image_tag])
    _execute_command(["docker", "cp", f"{temp_container}:/asset/", "greengrass-build"])
    _execute_command(["docker", "rm", temp_container])


def archive_build(directory_to_archive: str, output_filename: str):
    print(f"creating artifacts archive {output_filename} ...")
    shutil.make_archive(
        base_name=output_filename,
        format="zip",
        base_dir=".",
        root_dir=directory_to_archive,
    )
    print("... done archiving")


def create_artifacts(config: GdkConfig):
    """Creates the artifacts archive as a ZIP file"""

    do_build(config.component_name, config.component_version)
    archive_build(
        DIRECTORY_STAGING_ASSETS,
        os.path.join(
            DIRECTORY_OUTPUT_ARTIFACTS,
            config.component_name,
            config.component_version,
            FILE_ZIP_BASE,
        ),
    )


if __name__ == "__main__":
    config = GdkConfig()

    create_recipe(config)
    create_artifacts(config)
