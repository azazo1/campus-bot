# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'home_page.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_HomePage(object):
    def setupUi(self, HomePage):
        if not HomePage.objectName():
            HomePage.setObjectName(u"HomePage")
        HomePage.resize(400, 300)
        HomePage.setStyleSheet(u"")
        self.horizontalLayout = QHBoxLayout(HomePage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.homeTitleLabel = QLabel(HomePage)
        self.homeTitleLabel.setObjectName(u"homeTitleLabel")
        self.homeTitleLabel.setStyleSheet(u"font: bold 40px;")

        self.verticalLayout.addWidget(self.homeTitleLabel)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalWidget = QWidget(HomePage)
        self.verticalWidget.setObjectName(u"verticalWidget")
        self.verticalWidget.setMaximumSize(QSize(100, 16777215))
        self.verticalLayout_2 = QVBoxLayout(self.verticalWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.uiaLoginBtn = QPushButton(self.verticalWidget)
        self.uiaLoginBtn.setObjectName(u"uiaLoginBtn")

        self.verticalLayout_2.addWidget(self.uiaLoginBtn)

        self.quitBtn = QPushButton(self.verticalWidget)
        self.quitBtn.setObjectName(u"quitBtn")

        self.verticalLayout_2.addWidget(self.quitBtn)


        self.horizontalLayout_3.addWidget(self.verticalWidget)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.retranslateUi(HomePage)

        QMetaObject.connectSlotsByName(HomePage)
    # setupUi

    def retranslateUi(self, HomePage):
        HomePage.setWindowTitle(QCoreApplication.translate("HomePage", u"\u4e3b\u9875", None))
        self.homeTitleLabel.setText(QCoreApplication.translate("HomePage", u"ECNU \u6821\u56ed\u63d2\u4ef6", None))
        self.uiaLoginBtn.setText(QCoreApplication.translate("HomePage", u"\u767b\u5f55 UIA", None))
        self.quitBtn.setText(QCoreApplication.translate("HomePage", u"\u9000\u51fa\u5e94\u7528", None))
    # retranslateUi

