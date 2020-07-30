import os

from PySide2 import QtGui
from maya import cmds
import maya.mel as mel


class Assetize(object):
    def __init__(self):
        self.assets = {}
        self.placer_prefix = "PLCR"

    def generate_asset_name(self, filepath):
        """
        This method generates the name that would be used to create the Placers for the reference
        created.

        :return string: Asset Name if it was successfully generated.
        """
        if not os.path.exists(filepath):
            print "Invalid File: {0}".format(filepath)
            return "Invalid File: '{0}'".format(filepath)

        asset_name = "ASSET_{0}_{1}".format(
            os.path.splitext(os.path.basename(filepath))[0], self.placer_prefix
        )

        # TODO: Remove all special characters from the asset name
        return asset_name

    @staticmethod
    def construct_flavour(
        flavour_path,
        flavour_name="main",
        fg_color=(255, 255, 255, 255),
        bg_color=(0, 0, 0, 0),
    ):
        """

        :param string flavour_path: Path of the flavour file on the disk.
        :param string flavour_name: Name of the flavour that needs to be registered. Defaults to
                                    "main".
        :param tuple fg_color: Text Color to be assigned to the flavour. Defaults to Red.
        :param tuple bg_color: Background Color to be assigned to the flavour. Defaults to Red.

        :return dict: Packaged information in a data structure to be registered on the asset.
        """
        return {
            flavour_name: {
                "disk_path": flavour_path,
                "fg_color": fg_color,
                "bg_color": bg_color,
            }
        }

    def register_main_asset(
        self,
        asset_name,
        flavour_path,
        flavour_name="main",
        fg_color=(255, 255, 255, 255),
        bg_color=(0, 0, 0, 0),
    ):
        """
        Registers the main asset in the assets dict.

        {
            "<Asset Name>": {
                "flavours": {
                    "main": {
                        "<disk_path": "<path on disk>",
                        "fg_color": QtGui.QColor(255, 0, 0, 255),
                        "bg_color": QtGui.QColor(0, 0, 0, 0),
                    },
                    "<flavour_01>": {
                        "<disk_path": "<path on disk>",
                        "fg_color": QtGui.QColor(255, 0, 0, 255),
                        "bg_color": QtGui.QColor(0, 0, 0, 0),
                    }
                }
            }
        }

        :param string asset_name: Name of the asset that needs to be registered.
        :param string flavour_path: Path of the flavour file on the disk.
        :param string flavour_name: Name of the flavour that needs to be registered. Defaults to
                                    "main".
        :param tuple fg_color: Text Color to be assigned to the flavour. Defaults to Red.
        :param tuple bg_color: Background Color to be assigned to the flavour. Defaults to Red.
        """
        self.assets[asset_name] = {
            "flavours": self.construct_flavour(
                flavour_path=flavour_path,
                flavour_name=flavour_name,
                fg_color=fg_color,
                bg_color=bg_color,
            )
        }

        from pprint import pprint

        pprint(self.assets)

    def add_flavour(self, asset_name, flavour_name, flavour_path):
        """
        Add flavour to an existing asset.
        """
        self.assets[asset_name]["flavours"].update(
            self.construct_flavour(
                flavour_name=flavour_name,
                flavour_path=flavour_path,
                fg_color=(255, 0, 0, 255),
            )
        )

    def update_asset(
        self, asset_name, new_asset_name=None, asset_ref_path=None, fg_color=None
    ):

        if new_asset_name:
            self.assets[new_asset_name] = self.assets.get(asset_name)
            self.assets.pop(asset_name)
            cmds.rename(asset_name, new_asset_name)

        if asset_ref_path is not None:
            self.assets[asset_name]["asset_path"] = asset_ref_path

        if fg_color:
            self.assets[asset_name] = {
                "asset_path": asset_ref_path,
                "fg_color": fg_color,
            }

        print self.assets

    def deregister_asset(self, asset_name):
        self.assets.pop(asset_name)

    @staticmethod
    def create_asset_node(asset_name):
        new_circle = cmds.CreateNURBSCircle()
        asset_node = cmds.rename(new_circle, asset_name)

        cmds.scale(140.0, 140.0, 140.0)
        mel.eval(
            "select -r {0}.cv[0];select -add {0}.cv[2];select -add {0}.cv[4];select -add {0}.cv[6];"
            "scale -r -p 0cm 0cm 0cm 0.387573 1 0.387573 ;".format(asset_node)
        )

        return asset_node

    @staticmethod
    def delete_asset_node(asset_name):
        cmds.delete(asset_name)

    def save_assets(self):
        json_filepath = QtCore.QFileDialog

        with open(json_filepath, "w") as json_f:
            json.dump(dictionary_data, json_f, indent=4)
