"""

"""
# importing builtin modules
import os

# importing third party modules
from maya import cmds
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtCore, QtUiTools, QtWidgets

import assetize

reload(assetize)

REL_UI_FILE_PATH = r"ui\assetize.ui"


def maya_main_window():
    """
    This function gets the pointer to the Maya's Main window.
    Our window will be parented under this.
    """
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(long(pointer), QtWidgets.QWidget)


class AssetStandardItem(QtGui.QStandardItem):
    """
    Asset Item for the tree view to be populated. This would be created per asset that is populated.
    """

    def __init__(
        self,
        content,
        font_name="Open Sans",
        font_size=8,
        set_bold=False,
        set_editable=False,
        fg_color=QtGui.QColor(255, 255, 255, 255),
        bg_color=QtGui.QColor(0, 0, 0, 0),
    ):
        super(AssetStandardItem, self).__init__()

        font_object = QtGui.QFont(font_name, font_size)
        font_object.setBold(set_bold)

        self.setEditable = set_editable
        self.setFont(font_object)
        self.setForeground(QtGui.QBrush(fg_color))
        self.setBackground(QtGui.QBrush(bg_color))
        self.setText(content)


class AssetizeUI(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(
        self,
        assetize_backend,
        ui_file,
        main_width,
        main_height,
        parent=maya_main_window(),
    ):
        """
        Init method for the UI class.
        Initializes and sets up the UI.
        """
        # Initializing variables to be used later
        self.tree_model = QtGui.QStandardItemModel()
        self.assets_tree_root_node = None
        self.assetize_backend = assetize_backend
        self.current_selected_indexes = []
        self.current_asset_name = None

        super(AssetizeUI, self).__init__(parent)

        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(ui_file)
        uifile.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(uifile, parentWidget=self)
        uifile.close()

        main_grid_layout = QtWidgets.QGridLayout()
        main_grid_layout.addWidget(self.ui)
        self.setLayout(main_grid_layout)
        self.setGeometry(QtCore.QRect(0, 0, main_width, main_height))
        self.setWindowTitle("Assetize")

        # Centralizing the widget
        self.centralize_widget()

        # Setting up the UI Signal connections
        self.update_tree_view()
        self.setup_connections()

    @staticmethod
    def get_file_path_dialog(
        start_dir=os.path.expanduser("~"),
        file_filter="All Files *.*;;Maya Files (*.ma *.mb);;Alembic Files (*.abc)",
        caption="OK",
    ):
        """
        Opens up a new FIle Dialog to get the Asset FIle Path from the user.

        :return string: Path to the asset on disk as selected by the user.
        """
        file_paths = cmds.fileDialog2(
            startingDirectory=start_dir,
            fileFilter=file_filter,
            fileMode=1,
            okCaption=caption,
        )

        file_path = ""

        if file_paths is not None:
            file_path = file_paths[0]

        return file_path

    def centralize_widget(self):
        """
        This method is responsible for centralising the widget on the screen.
        """
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setup_connections(self):
        """
        Setup all your UI actions within this method.
        self.ui would be having all the UI elements to modify.
        """
        self.ui.pushButton_add_asset.clicked.connect(self.action_add_asset)
        self.ui.pushButton_remove_asset.clicked.connect(self.action_remove_asset)
        self.ui.pushButton_add_flavour.clicked.connect(self.action_add_flavour)
        self.ui.pushButton_bring_em_in.clicked.connect(self.action_update_asset)

        self.ui.treeView_assets.selectionModel().selectionChanged.connect(
            self.selection_changed
        )
        self.tree_model.itemChanged.connect(self.asset_modified)

    def selection_changed(self):
        """
        Gets triggered every time the selection in the treeView_assets is changed.
        Since this would event would be triggered more often than others. Try to keep the
        computations minimal.
        """
        self.current_selected_indexes = self.ui.treeView_assets.selectedIndexes()

        if len(self.current_selected_indexes) == 1:
            self.current_asset_name = (
                self.current_selected_indexes[0]
                .model()
                .itemFromIndex(self.current_selected_indexes[0])
                .text()
            )

    def asset_modified(self):
        """
        Gets triggered every time an item in the tree model is changed.
        """
        self.assetize_backend.update_asset(
            asset_name=self.current_asset_name,
            new_asset_name=self.current_selected_indexes[0]
            .model()
            .itemFromIndex(self.current_selected_indexes[0])
            .text(),
        )

    def update_tree_view(self):
        """
        Sets up the initial tree view to which items could be aded later.
        """
        self.tree_model.clear()

        self.assets_tree_root_node = self.tree_model.invisibleRootItem()
        self.ui.treeView_assets.setModel(self.tree_model)

        for asset in self.assetize_backend.assets:
            # Creating an Asset Tree Item to attach to the tree view
            asset_item = AssetStandardItem(asset)

            for asset_info in self.assetize_backend.assets[asset]["flavours"]:
                # Creating an Asset Tree Item to attach to the tree view
                asset_info_item = AssetStandardItem(asset_info)

                asset_item.appendRow(asset_info_item)

            self.assets_tree_root_node.appendRow(asset_item)

        self.ui.treeView_assets.expandAll()

    def action_add_asset(self):
        """
        Performs all necessary operations for the adding an asset.
        For now, it mean, that it adds the asset to the assets list in assetize_backend object
        and adds the asset to the UI tree.
        """
        asset_creation_successful = 0

        try:
            # Getting the asset path input from the user
            flavour_disk_path = self.get_file_path_dialog()

            if flavour_disk_path is None:
                return

            if not flavour_disk_path or not os.path.exists(flavour_disk_path):
                raise ValueError("INVALID REFERENCE - {0}".format(flavour_disk_path))

            # Generating the asset name from on the file name
            asset_name = self.assetize_backend.generate_asset_name(flavour_disk_path)

            # This will override the asset name based on the actual asset node created in the scene
            asset_name = self.assetize_backend.create_asset_node(asset_name)

            asset_creation_successful = 1
        except Exception as err:
            # TODO: Try to not keep it this broad of an exception
            raise err

        if asset_creation_successful:
            # Registering only if the asset creation in the scene was successful
            self.assetize_backend.register_main_asset(
                asset_name, flavour_disk_path, fg_color=(255, 0, 0, 255)
            )
            self.update_tree_view()

    def request_flavour_name(self, msg):
        cmds.promptDialog(title="Add Flavour", message=msg, button=["Create Flavour"])

        return cmds.promptDialog(q=1, tx=1)

    def action_add_flavour(self):
        """
        Performs all necessary actions to register a flavour on the selected asset.

        :return:
        """
        if self.current_asset_name not in self.assetize_backend.assets.keys():
            raise ValueError("INVALID ASSET - {0}".format(self.current_asset_name))

        flavour_name = self.request_flavour_name(
            msg="ADDING FLAVOUR ON - {1}\n{0}\nGive this Flavour a Name.\t\t\t\t".format(
                "-" * 60, self.current_asset_name
            )
        )

        while True:
            if (
                flavour_name
                in self.assetize_backend.assets[self.current_asset_name][
                    "flavours"
                ].keys()
            ):

                flavour_name = self.request_flavour_name(
                    msg="ADDING FLAVOUR ON - {1}\n{0}\nFlavour already exists - '{2}'\t\t"
                    "\t\t\nEnter a New Name".format(
                        "-" * 60, self.current_asset_name, flavour_name
                    )
                )
            elif flavour_name == "":
                print "UNABLE TO CREATE FLAVOUR. Flavour Name cannot be empty."
                return
            else:
                break

        self.assetize_backend.add_flavour(
            asset_name=self.current_asset_name,
            flavour_name=flavour_name,
            flavour_path="Empty",
        )

        self.update_tree_view()

    def action_remove_asset(self):
        """
        Removes the Asset from the scene and de-registers from the backend data structure.
        """
        for selected_index in self.current_selected_indexes:

            selected_asset_name = (
                selected_index.model().itemFromIndex(selected_index).text()
            )
            self.assetize_backend.delete_asset_node(selected_asset_name)
            self.assetize_backend.deregister_asset(selected_asset_name)
            self.tree_model.removeRow(1, selected_index)

        self.update_tree_view()

    def action_update_asset(self):
        """

        :return:
        """
        selected_indexes = self.ui.treeView_assets.selectedIndexes()

        for selected_index in selected_indexes:
            selected_asset_name = (
                selected_index.model().itemFromIndex(selected_index).text()
            )
            self.assetize_backend.update_asset(
                selected_asset_name, fg_color=(0, 255, 0, 255)
            )

        self.update_tree_view()


def get_ui_file():
    """
    Gets the absolute ui file path from the curent project directory

    :return: The absolute file path to the UI file.
    """
    curr_dir = os.path.dirname(__file__)
    return os.path.join(os.path.split(curr_dir)[0], REL_UI_FILE_PATH)


def main(width=950, height=530):
    """
    Main function to be called if this modules is to be imported and used.

    :param int width: Desired width of the window that would be drawn.
    :param int height: Desired height of the window that would be drawn.
    """
    # If the UI already exists, closes it before proceeding
    global my_ui
    try:
        my_ui.close()
    except:
        pass

    ui_file = get_ui_file()

    if not os.path.exists(ui_file):
        raise IOError(
            "UI file path could not be resolved properly. Please make sure the package "
            "is complete.\nResolved UI File was - {0}".format(ui_file)
        )

    assetize_backend = assetize.Assetize()

    my_ui = AssetizeUI(assetize_backend, ui_file, width, height)
    my_ui.show(dockable=True)


if __name__ == "__main__":
    width = 430
    height = 550

    main(width, height)
