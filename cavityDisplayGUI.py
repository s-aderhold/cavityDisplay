from dataclasses import dataclass

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout
from epics import PV
from functools import partial
from pydm import Display
from pydm.widgets import PyDMEmbeddedDisplay, PyDMRelatedDisplayButton, PyDMTemplateRepeater
from typing import List

from cavityWidget import CavityWidget
from lcls_tools.devices.scLinac import LINAC_OBJECTS

STATUS_SUFFIX = "CUDSTATUS"
SEVERITY_SUFFIX = "CUDSEVR"

GREEN_FILL_COLOR = QColor(9, 141, 0)
YELLOW_FILL_COLOR = QColor(244, 230, 67)
RED_FILL_COLOR = QColor(150, 0, 0)
PURPLE_FILL_COLOR = QColor(131, 61, 235)
GRAY_FILL_COLOR = QColor(127, 127, 127)

BLACK_TEXT_COLOR = QColor(0, 0, 0)
DARK_GRAY_COLOR = QColor(40, 40, 40)
WHITE_TEXT_COLOR = QColor(250, 250, 250)

DARK_PURPLE_COLOR = QColor(106, 102, 212)
ALTERNATE_YELLOW_COLOR = QColor(223, 149, 0)


@dataclass
class ShapeParameters:
    fillColor: QColor
    borderColor: QColor
    numPoints: int
    rotation: float


SHAPE_PARAMETER_DICT = {0: ShapeParameters(GREEN_FILL_COLOR, GREEN_FILL_COLOR,
                                           4, 0),
                        1: ShapeParameters(YELLOW_FILL_COLOR, YELLOW_FILL_COLOR,
                                           3, 0),
                        2: ShapeParameters(RED_FILL_COLOR, RED_FILL_COLOR,
                                           6, 0),
                        3: ShapeParameters(PURPLE_FILL_COLOR, PURPLE_FILL_COLOR,
                                           20, 0),
                        4: ShapeParameters(GRAY_FILL_COLOR, GRAY_FILL_COLOR,
                                           10, 0)}


class CavityDisplayGUI(Display):

    def __init__(self, parent=None, args=None):
        super().__init__(parent=parent, args=args,
                         ui_filename="frontend/cavityDisplay.ui")

        embeddedDisplays: List[PyDMEmbeddedDisplay] = [self.ui.L0B,
                                                       self.ui.L1B,
                                                       self.ui.L2B,
                                                       self.ui.L3B]

        for index, linacEmbeddedDisplay in enumerate(embeddedDisplays):
            linacEmbeddedDisplay.loadWhenShown = False
            linacObject = LINAC_OBJECTS[index]
            print("loading {linac}".format(linac=linacObject.name))

            linacHorizLayout = linacEmbeddedDisplay.findChild(QHBoxLayout)
            totalCryosInLinac = linacHorizLayout.count()

            # linac will be a list of cryomodules
            cryoDisplayList: List[Display] = []
            for itemIndex in range(totalCryosInLinac):
                cryoDisplayList.append(linacHorizLayout.itemAt(itemIndex).widget())

            for cryomoduleDisplay in cryoDisplayList:
                cmButton: PyDMRelatedDisplayButton = cryomoduleDisplay.children()[1]

                cmTemplateRepeater: PyDMTemplateRepeater = cryomoduleDisplay.children()[2]

                cryomoduleObject = linacObject.cryomodules[str(cmButton.text())]
                cavityWidgetList: List[CavityWidget] = cmTemplateRepeater.findChildren(CavityWidget)

                for cavityWidget in cavityWidgetList:
                    cavityObject = cryomoduleObject.cavities[int(cavityWidget.cavityText)]

                    severityPV = PV(cavityObject.pvPrefix + SEVERITY_SUFFIX)
                    statusPV = PV(cavityObject.pvPrefix + STATUS_SUFFIX)

                    # This line is meant to initialize the cavityWidget colors and shapes when first launched
                    self.severityCallback(cavityWidget, severityPV.value)
                    self.statusCallback(cavityWidget, statusPV.value)

                    # .add_callback is called when severityPV changes value
                    severityPV.add_callback(partial(self.severityCallback, cavityWidget))

                    # .add_callback is called when statusPV changes value
                    statusPV.add_callback(partial(self.statusCallback, cavityWidget))

    # Updates shape depending on pv value
    def severityCallback(self, cavity_widget, value, **kw):
        self.changeShape(cavity_widget,
                         SHAPE_PARAMETER_DICT[value]
                         if value in SHAPE_PARAMETER_DICT
                         else SHAPE_PARAMETER_DICT[3])

    # Change PyDMDrawingPolygon color
    @staticmethod
    def changeShape(cavity_widget, shapeParameterObject):
        cavity_widget.brush.setColor(shapeParameterObject.fillColor)
        cavity_widget.penColor = shapeParameterObject.borderColor
        cavity_widget.numberOfPoints = shapeParameterObject.numPoints
        cavity_widget.rotation = shapeParameterObject.rotation

    # Change cavity label
    @staticmethod
    def statusCallback(cavity_widget, value, **kw):
        cavity_widget.cavityText = value
