import json
from typing import Dict, List, Literal, TypedDict, Union


class GdkConfigComponentPublish(TypedDict):
    bucket: str
    region: str


class GdkConfigComponentBuild(TypedDict):
    build_system: Literal["zip", "custom"]
    custom_build_command: Union[str, List[str]]


class GdkConfigComponent(TypedDict):
    author: str
    version: str
    build: GdkConfigComponentBuild
    publish: GdkConfigComponentPublish


class GdkConfigJson(TypedDict):
    component: Dict[str, GdkConfigComponent]
    gdk_version: str


class GdkConfig:
    def __init__(self) -> None:
        with open("gdk-config.json", "r") as fid:
            self._config: GdkConfigJson = json.load(fid)
        self._name = None

    @property
    def component_name(self):
        if self._name is None:
            self._name = list(self._config.get("component").keys())[0]

        return self._name

    @property
    def component_version(self):
        return self._config.get("component").get(self.component_name).get("version")

    @property
    def component_author(self):
        return self._config.get("component").get(self.component_name).get("author")

    @property
    def publish_bucket(self):
        return self._config.get("component").get(self.component_name).get("publish").get("bucket")
