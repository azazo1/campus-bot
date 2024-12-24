# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'config_item_row.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_configItemRow(object):
    def setupUi(self, configItemRow):
        if not configItemRow.objectName():
            configItemRow.setObjectName(u"configItemRow")
        configItemRow.resize(152, 88)
        self.vl2 = QVBoxLayout(configItemRow)
        self.vl2.setObjectName(u"vl2")
        self.hl = QHBoxLayout()
        self.hl.setObjectName(u"hl")
        self.vl = QVBoxLayout()
        self.vl.setObjectName(u"vl")
        self.itemName = QLabel(configItemRow)
        self.itemName.setObjectName(u"itemName")
        self.itemName.setStyleSheet(u"font: bold 15px;")

        self.vl.addWidget(self.itemName)

        self.itemDesc = QLabel(configItemRow)
        self.itemDesc.setObjectName(u"itemDesc")
        self.itemDesc.setStyleSheet(u"font: italic 13px;\n"
"margin-left: 15px;")

        self.vl.addWidget(self.itemDesc)


        self.hl.addLayout(self.vl)

        self.hs = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl.addItem(self.hs)

        self.inlineContent = QVBoxLayout()
        self.inlineContent.setObjectName(u"inlineContent")

        self.hl.addLayout(self.inlineContent)


        self.vl2.addLayout(self.hl)

        self.hl2 = QHBoxLayout()
        self.hl2.setObjectName(u"hl2")
        self.hs2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl2.addItem(self.hs2)

        self.largeContent = QVBoxLayout()
        self.largeContent.setObjectName(u"largeContent")

        self.hl2.addLayout(self.largeContent)


        self.vl2.addLayout(self.hl2)


        self.retranslateUi(configItemRow)

        QMetaObject.connectSlotsByName(configItemRow)
    # setupUi

    def retranslateUi(self, configItemRow):
        configItemRow.setWindowTitle(QCoreApplication.translate("configItemRow", u"configItemRow", None))
        self.itemName.setText(QCoreApplication.translate("configItemRow", u"itemName", None))
        self.itemDesc.setText(QCoreApplication.translate("configItemRow", u"itemDesc", None))
    # retranslateUi

