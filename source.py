import copy
from math import log, sqrt, pi
from decimal import Decimal
from typing import Optional, Dict

CONVERSION_DBA = {
    0.3: -85.4,
    8.0: -77.8,
    10.0: -70.4,
    12.5: -63.4,
    16.0: -56.7,
    20.0: -50.5,
    25.0: -44.7,
    31.5: -39.4,
    40.0: -34.6,
    50.0: -30.2,
    63.0: -26.2,
    80.0: -22.5,
    100.0: -19.1,
    125.0: -16.1,
    160.0: -13.4,
    200.0: -10.9,
    250.0: -8.6,
    315.0: -6.6,
    400.0: -4.8,
    500.0: -3.2,
    630.0: -1.9,
    800.0: -0.8,
    1000.0: 0.0,
    1250.0: 0.6,
    1600.0: 1.0,
    2000.0: 1.2,
    2500.0: 1.3,
    3150.0: 1.2,
    4000.0: 1.0,
    5000.0: 0.5,
    6300.0: -0.1,
    8000.0: -1.1,
    10000.0: -2.5,
    12500.0: -4.3,
    16000.0: -6.6,
    20000.0: -9.3,
}

BANDE_DE_TIERS_DOCTAVE = [
    25,
    31.5,
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
    6300,
    8000,
    10000,
    12500,
    16000,
    20000,
]


class Source:
    """Définition d'une source acoustique"""

    def __init__(self, unit, nb: int, spec: str, start: float):
        """
        args:
            nb: nombre de valeurs de niveau acoustique
            spec: type de division spectrale
            start: fréquence la plus basse (sauf pour une valeur unique)

        """
        self.unit: Optional[str] = unit
        self.type = None
        self.puissances: Dict[float, float]
        if spec == "Bandes d'octave":
            self.puissances = {start * (2 ** i): 0 for i in range(nb)}
        elif spec == "Bandes de tiers d'octave":
            start_index = BANDE_DE_TIERS_DOCTAVE.index(start)
            frequences_portion = BANDE_DE_TIERS_DOCTAVE[start_index : start_index + nb]
            self.puissances = {freq: 0 for freq in frequences_portion}
        elif spec == "Valeur unique":
            self.puissances = {}
        else:
            raise NotImplementedError()

    def convert_unit(self):
        """conversion de dB à dBA"""
        if self.unit == "dB":
            ponderation_A = {
                k: v
                for (k, v) in CONVERSION_DBA.items()
                if k in common_keys(self.puissances, CONVERSION_DBA)
            }
            for key in ponderation_A.keys():
                self.puissances[key]=int(self.puissances[key])
                self.puissances[key] += ponderation_A[key]
            self.unit = "dBA"

    def __str__(self):
        return str(self.puissances)

    def niveau_global_spectral(self, source):
        source_somme = copy.deepcopy(self)

        for k in self.puissances.keys():
            source_somme.puissances[k] = niveau_global(
                float(self.puissances[k]), float(source.puissances[k])
            )
        return source_somme

    def convert_puissance(self):
        """ convertit un niveau de pression en niveau acoustique"""
        pass


class Mesure:
    """définition des conditions de mesure"""

    def __init__(self, source):

        self.mesure_direct = {k: v for (k, v) in source.puissances.items()}
        self.mesure_indirect = {k: v for (k, v) in source.puissances.items()}
        self.mesure_totale = {}
        self.distance = 0
        self.directivite = 1
        self.volume_x = 0
        self.volume_y = 0
        self.volume_z = 0
        self.materiau = {}

    def niveau_pression_direct(self) -> dict:
        """ renvoie le niveau de pression acoustique en dBA à la distance r avec une directivité q"""
        for k in self.mesure_direct.keys():
            self.mesure_direct[k] = distance(
                self.mesure_direct[k], self.distance
            ) + 10 * log(self.directivite, 10)
        return self.mesure_direct

    def niveau_pression_indirect(self):
        self.mesure_indirect = convert_freq(
            self.mesure_indirect, common_keys(self.mesure_indirect, self.materiau)
        )
        for k in self.mesure_indirect.keys():
            self.mesure_indirect[k] = self.mesure_indirect[k] + 10 * log(
                4
                / (
                    surface(self.volume_x, self.volume_y, self.volume_z)
                    * self.materiau[k]
                    / (1 - self.materiau[k])
                ),
                10,
            )
        return self.mesure_indirect

    def niveau_pression_totale(self):
        convert_freq(
            self.mesure_direct, common_keys(self.mesure_direct, self.mesure_indirect)
        )
        convert_freq(
            self.mesure_indirect, common_keys(self.mesure_direct, self.mesure_indirect)
        )
        self.mesure_totale = copy.deepcopy(self.mesure_direct)

        for k in self.mesure_totale.keys():
            self.mesure_totale[k] = self.mesure_direct[k] + self.mesure_indirect[k]
        for k in self.mesure_totale.keys():
            if self.mesure_totale[k] < 0:
                self.mesure_totale[k] = 0
        return self.mesure_totale


def distance(l_w: float, r: float) -> float:
    """calcul de l'atténuation due à la distance"""
    l_w = Decimal(l_w)
    r = Decimal(r)
    l_p = l_w + 10 * (1 / (4 * Decimal(pi) * (r ** 2))).log10()
    return float(l_p)


def surface(x, y, z):
    surface = 2 * (x * y + y * z + x * z)
    return surface


def niveau_global(lw_1: float, lw_2: float) -> float:
    """Somme logarithmique de deux sources"""
    lw_1 = Decimal(lw_1)
    lw_2 = Decimal(lw_2)
    lw_global = 10 * (10 ** (lw_1 / 10) + 10 ** (lw_2 / 10)).log10()
    return float(lw_global)


def convert_freq(dict1: dict, common_keys: dict) -> dict:
    """supprime les valeurs en trop pour obtenir une plage de fréquences communes à toutes les sources"""
    dict1 = {k: v for (k, v) in dict1.items() if k in common_keys}

    return dict1


def common_keys(dict1, dict2):
    """renvoie les clés communes de 2 dictionnaires"""
    return sorted(list(set(dict1.keys()).intersection(set(dict2.keys()))))


# penser au cas particulier où la source n'a qu'une seule valmeur de puissance sonore
# penser à faire un convert_unit après avoir récupéré les valeurs entrée par l'utilisateur
# penser à faire un correctif final pour ne pas avoir de valeur négative de pression acoustique
# penser à faire un fichier dédié aux constantes, notamment auc constantes d'absorption acoustique

if __name__ == "__main__":
    s1 = Source(8, "bande d'octave", 250)
    s2 = Source(20, "tiers d'octave", 50)
    print("s1_init =", s1)
    print("s2_init =", s2)

    s1.puissances[250] = 1
    s1.puissances[500] = 2
    s1.puissances[1000] = 3
    s1.puissances[2000] = 5
    s1.puissances[4000] = 8
    s1.puissances[8000] = 13
    s1.puissances[16000] = 21
    s1.puissances[32000] = 34

    s2.puissances[50] = 0
    s2.puissances[63] = 1
    s2.puissances[80] = 1
    s2.puissances[100] = 2
    s2.puissances[125] = 3
    s2.puissances[160] = 5
    s2.puissances[200] = 8
    s2.puissances[250] = 13
    s2.puissances[315] = 21
    s2.puissances[400] = 34
    s2.puissances[500] = 55
    s2.puissances[630] = 89
    s2.puissances[800] = 144
    s2.puissances[1000] = 233
    s2.puissances[1250] = 377
    s2.puissances[1600] = 610
    s2.puissances[2000] = 987
    s2.puissances[2500] = 1597
    s2.puissances[3150] = 2584
    s2.puissances[4000] = 4181

    print("s1_val =", s1)
    print("s2_val =", s2)

    s1.puissances = convert_freq(
        s1.puissances, common_keys(s1.puissances, s2.puissances)
    )
    s2.puissances = convert_freq(
        s2.puissances, common_keys(s1.puissances, s2.puissances)
    )

    print("s1_conv =", s1)
    print("s2_conv =", s2)
    s = s1.niveau_global_spectral(s2)
    print("s=", s)

    m1 = Mesure(s)
    print("m1_direct_init=", m1.mesure_direct)
    print("m1_indirect_init=", m1.mesure_indirect)
    m1.distance = 2
    m1.directivite = 2
    print("m1 direct=", m1.niveau_pression_direct())
    m1.materiau[125] = 0.3
    m1.materiau[250] = 0.4
    m1.materiau[500] = 0.6
    m1.materiau[1000] = 0.6
    m1.materiau[2000] = 0.5
    m1.materiau[4000] = 0.5
    print("m1_materiau=", m1.materiau)
    m1.volume_x = 3
    m1.volume_y = 2
    m1.volume_z = 4

    print("m1_indirect=", m1.niveau_pression_indirect())
    print("niveau_pression_totale=", m1.niveau_pression_totale())
