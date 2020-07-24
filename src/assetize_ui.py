"""


"""
# importing builtin modules
import os

# importing third party modules
from maya import cmds
import maya.OpenMayaUI as omui
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
    def __init__(
        self,
        content,
        font_name="Open Sans",
        font_size=8,
        set_bold=False,
        set_editable=False,
        fg_color=QtGui.QColor(0, 0, 0, 0),
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


class AssetizeUI(QtWidgets.QDialog):
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

    def update_tree_view(self):
        """
        Sets up the initial tree view to which items could be aded later.

        :return:
        """
        self.tree_model.clear()

        self.assets_tree_root_node = self.tree_model.invisibleRootItem()
        self.ui.treeView_assets.setModel(self.tree_model)

        for asset in self.assetize_backend.assets:
            # Creating an Asset Tree Item to attach to the tree view
            asset_item = AssetStandardItem(
                asset, fg_color=(QtGui.QColor(255, 0, 0, 255))
            )

            self.assets_tree_root_node.appendRow(asset_item)

    def action_add_asset(self):
        """
        Performs all necessary operations for the adding an asset.
        For now, it mean, that it adds the asset to the assets list in assetize_backend object
        and adds the asset to the UI tree.
        """
        asset_creation_succesful = 0

        try:
            # Getting the asset path input from the user
            asset_ref_path = self.get_asset_path_dialog()

            if asset_ref_path is None:
                return

            if not asset_ref_path or not os.path.exists(asset_ref_path):
                raise ValueError("INVALID REFERENCE - {0}".format(asset_ref_path))

            # Generating the asset name from on the file name
            asset_name = self.assetize_backend.generate_asset_name(asset_ref_path)

            # This will override the asset name based on the actual asset node created in the scene
            asset_name = self.assetize_backend.create_asset_node(asset_name)

            asset_creation_succesful = 1
        except Exception as err:
            raise err

        if asset_creation_succesful:
            # Registering
            self.assetize_backend.register_asset(asset_name, asset_ref_path)
            self.update_tree_view()

    def action_remove_asset(self):
        """
        Removes the Asset from the scene and de-registers from the backend data structure.
        """
        selected_indexes = self.ui.treeView_assets.selectedIndexes()

        for selected_index in selected_indexes:
            selected_asset_name = selected_index.model().itemFromIndex(selected_index).text()
            self.assetize_backend.delete_asset_node(selected_asset_name)
            self.assetize_backend.deregister_asset(selected_asset_name)
            self.tree_model.removeRow(1, selected_index)

        self.update_tree_view()

    @staticmethod
    def get_asset_path_dialog():
        """
        Opens up a new FIle Dialog to get the Asset FIle Path from the user.

        :return string: Path to the asset on disk as selected by the user.
        """
        asset_path = cmds.fileDialog2(
            startingDirectory=os.path.expanduser("~"),
            fileFilter="All Files *.*;;Maya Files (*.ma *.mb);;Alembic Files (*.abc)",
            fileMode=1,
            okCaption="Add Asset",
        )

        if asset_path is not None:
            asset_path = asset_path[0]

        return asset_path


def get_ui_file():
    """
    Gets the absolute ui file path from the curent project directory

    :return: The absolute file path to the UI file.
    """
    curr_dir = os.path.dirname(__file__)
    return os.path.join(os.path.split(curr_dir)[0], REL_UI_FILE_PATH)


def main(width=430, height=550):
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
    my_ui.show()


if __name__ == "__main__":
    width = 430
    height = 550

    main(width, height)
