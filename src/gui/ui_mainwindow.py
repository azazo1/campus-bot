# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(900, 450)
        self.verticalLayout = QVBoxLayout(MainWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.majorHorizontal = QHBoxLayout()
        self.majorHorizontal.setObjectName(u"majorHorizontal")
        self.pageSelectArea = QVBoxLayout()
        self.pageSelectArea.setSpacing(6)
        self.pageSelectArea.setObjectName(u"pageSelectArea")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageSelectArea.addItem(self.verticalSpacer)

        self.homePageBtn = QPushButton(MainWindow)
        self.homePageBtn.setObjectName(u"homePageBtn")

        self.pageSelectArea.addWidget(self.homePageBtn)

        self.pluginPageBtn = QPushButton(MainWindow)
        self.pluginPageBtn.setObjectName(u"pluginPageBtn")

        self.pageSelectArea.addWidget(self.pluginPageBtn)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageSelectArea.addItem(self.verticalSpacer_2)


        self.majorHorizontal.addLayout(self.pageSelectArea)

        self.pageContainer = QStackedWidget(MainWindow)
        self.pageContainer.setObjectName(u"pageContainer")
        self.pageContainer.setStyleSheet(u"QStackedWidget {\n"
"    border: 2px solid #909090;\n"
"    border-radius: 10px;\n"
"}")
        self.homePage = QWidget()
        self.homePage.setObjectName(u"homePage")
        self.pageContainer.addWidget(self.homePage)
        self.pluginPage = QWidget()
        self.pluginPage.setObjectName(u"pluginPage")
        self.pageContainer.addWidget(self.pluginPage)

        self.majorHorizontal.addWidget(self.pageContainer)


        self.verticalLayout.addLayout(self.majorHorizontal)


        self.retranslateUi(MainWindow)

        self.pageContainer.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"ECNU\u6821\u56ed\u63d2\u4ef6", None))
        self.homePageBtn.setText(QCoreApplication.translate("MainWindow", u"\u4e3b\u9875", None))
        self.pluginPageBtn.setText(QCoreApplication.translate("MainWindow", u"\u63d2\u4ef6\u914d\u7f6e", None))
    # retranslateUi

