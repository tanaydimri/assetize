import os

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

        asset_name_raw = "ASSET_{0}_{1}".format(
            os.path.splitext(os.path.basename(filepath))[0], self.placer_prefix
        )

        counter = 0
        asset_name = asset_name_raw

        while True:
            if asset_name in self.assets.keys():
                counter += 1
                counter_string = str(counter).zfill(2)
                asset_name = "{0}_{1}".format(asset_name_raw, counter_string)
            else:
                break

        # TODO: Remove all special characters from the asset name
        return asset_name

    def register_asset(self, asset_name, asset_ref_path):
        self.assets[asset_name] = asset_ref_path

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
