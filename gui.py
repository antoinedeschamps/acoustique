# Filename: gui.py
import sys

from source import (
    Source,
    Mesure,
    distance,
    surface,
    niveau_global,
    convert_freq,
    common_keys,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QWidget,
    QPushButton,
    QStackedWidget,
    QMainWindow,
    QLabel,
)


def combo_dB():
    combobox = QComboBox()
    combobox.addItems(["dB", "dBA"])
    return combobox


def combo_spec():
    combobox = QComboBox()
    combobox.addItems(["Valeur unique", "Bandes de tiers d'octave", "Bandes d'octave"])
    return combobox


def line_init(layout, line_number: int):
    label_source = QLabel(f"Source {line_number + 1}")
    label_source.setFont(BoldFont)
    label_unit = QLabel("Unité:")
    label_freq = QLabel("Division")
    label_nb = QLabel("Nombre de Valeurs")
    label_start = QLabel("Fréquence de départ")
    combobox_db = combo_dB()
    combobox_spec = combo_spec()
    lineedit_nb_valeur = QLineEdit()
    lineedit_freq_start = QLineEdit()
    layout.addWidget(label_source, line_number, 0)
    layout.addWidget(label_unit, line_number, 1)
    layout.addWidget(combobox_db, line_number, 2)
    layout.addWidget(label_freq, line_number, 3)
    layout.addWidget(combobox_spec, line_number, 4)
    layout.addWidget(label_nb, line_number, 5)
    layout.addWidget(lineedit_nb_valeur, line_number, 6)
    layout.addWidget(label_start, line_number, 7)
    layout.addWidget(lineedit_freq_start, line_number, 8)
    return {
        "combobox_db": combobox_db,
        "combobox_spec": combobox_spec,
        "lineedit_nb_valeur": lineedit_nb_valeur,
        "lineedit_freq_start": lineedit_freq_start,
    }


def show_field_nb():
    win_nb = QWidget()
    mwin.setCentralWidget(win_nb)
    win_nb.setWindowTitle("Définition des sources (1/3): Nombre de sources")
    layout_nb = QFormLayout()
    textbox_nbs = QLineEdit()
    layout_nb.addRow("Entrer le nombre de sources acoustiques:", textbox_nbs)
    button_nb = QPushButton("Ok")
    layout_nb.addWidget(button_nb)

    def handler_nb():
        textboxValue_nbs = textbox_nbs.text()
        textboxValue_nbs = int(textboxValue_nbs)
        show_fields_init(textboxValue_nbs)

    button_nb.clicked.connect(handler_nb)
    win_nb.setLayout(layout_nb)
    win_nb.show()


def show_fields_init(textboxValue_nbs: int):
    win_init = QWidget()
    win_init.setWindowTitle("Définition des sources (2/3): Type de valeurs")
    mwin.setCentralWidget(win_init)
    layout_init = QGridLayout()
    lines = []
    for n in range(textboxValue_nbs):
        dico = line_init(layout_init, n)
        lines.append(dico)
    button_init = QPushButton("Ok")
    layout_init.addWidget(button_init, textboxValue_nbs + 1, 4)

    def handler_init():
        unit = [line["combobox_db"].currentText() for line in lines]
        nb = [line["lineedit_nb_valeur"].text() for line in lines]
        spec = [line["combobox_spec"].currentText() for line in lines]
        start = [line["lineedit_freq_start"].text() for line in lines]
        show_fields_values(unit, nb, spec, start)

    button_init.clicked.connect(handler_init)
    win_init.setLayout(layout_init)
    win_init.show()


def show_fields_values(units: list, nbs: list, specs: list, starts: list):
    win_values = QWidget()
    win_values.setWindowTitle("Définition des sources (3/3): Entrée des valeurs ")
    mwin.setCentralWidget(win_values)
    layout_values = QGridLayout()
    button_values = QPushButton("Ok")
    nbs = [int(elem) for elem in nbs]
    layout_values.addWidget(button_values, max(nbs) + 1, 0)
    sources = []

    for unit, nb, spec, start in zip(units, nbs, specs, starts):
        source = Source(unit, int(nb), spec, float(start))
        sources.append(source)

    for index_source, source in enumerate(sources):
        source.qlineedits = {}
        label_source = QLabel(f"Source {index_source + 1}")
        label_source.setFont(BoldFont)
        label_source.setAlignment(Qt.AlignCenter)
        layout_values.addWidget(label_source, 0, index_source * 2, 1, 2)
        frequence = list(source.puissances.keys())
        for index_freq, freq in enumerate(frequence):
            label_freq = QLabel(str(freq) + " Hz")
            label_freq.setAlignment(Qt.AlignCenter)
            puissance = QLineEdit()
            source.qlineedits[freq] = puissance
            layout_values.addWidget(label_freq, index_freq + 1, index_source * 2)
            layout_values.addWidget(puissance, index_freq + 1, index_source * 2 + 1)

    def handler_values():
        for source in sources:
            for k in source.qlineedits.keys():
                source.puissances[k] = source.qlineedits[k].text()
        puiss = sources[0].puissances
        for source in sources:
            puiss = convert_freq(puiss, source.puissances)
        for source in sources:
            source.puissances = convert_freq(source.puissances, puiss)
            source.convert_unit()
        somme = sources[0]
        for source in sources:
            del source.qlineedits
            somme = somme.niveau_global_spectral(source)
        print(somme)
        show_fields_mesure(somme)

    button_values.clicked.connect(handler_values)
    win_values.setLayout(layout_values)
    win_values.show()


def show_fields_mesure(somme):
    win_mesure = QWidget()
    mwin.setCentralWidget(win_mesure)
    layout_mesure = QFormLayout()
    distance = QLineEdit()
    layout_mesure.addRow("Entrer la distance à la source:", distance)
    directivite = QComboBox()
    directivite.addItems(["0", "1", "2"])
    layout_mesure.addRow("Entrer la directivité",directivite)
    button_mesure = QPushButton("Ok")
    layout_mesure.addWidget(button_mesure)
    mesure = Mesure(somme)

    def handler_mesure():
        mesure.distance = distance.text()
        mesure.directivite = int(directivite.currentText())
        show_result(mesure.niveau_pression_direct())

    button_mesure.clicked.connect(handler_mesure)
    win_mesure.setLayout(layout_mesure)
    win_mesure.show()

def show_result(result):
    win_result = QWidget()
    mwin.setCentralWidget(win_result)
    layout_result = QGridLayout()
    for index,(k,v) in enumerate(result.items()):
        label_f = QLabel(str(k))
        layout_result.addWidget(label_f,index,0)
        label_p = QLabel(str(v))
        layout_result.addWidget(label_p,index, 1)
    win_result.setLayout(layout_result)
    win_result.show()

app = QApplication(sys.argv)
mwin = QMainWindow()
show_field_nb()
BoldFont = QFont()
BoldFont.setBold(True)


mwin.show()

sys.exit(app.exec())

# newwind

