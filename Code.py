import simpy
import random
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
import numpy as np

class Proizvod:
    def __init__(self, ime, vrijeme_obrade, prioritet):
        self.ime = ime
        self.vrijeme_obrade = vrijeme_obrade
        self.prioritet = prioritet
        self.faza = ["Prijem"]  # Inicijalna faza: Prijem

    def azuriraj_fazu(self, faza):
        self.faza.append(faza)

class TransportnoVozilo:
    def __init__(self, env, distributivni_centar):
        self.env = env
        self.distributivni_centar = distributivni_centar
        self.vozilo = simpy.Resource(env, capacity=1)

    def prevezi_proizvod(self, porudzbina):
        yield self.env.timeout(random.uniform(1, 3))  # Simulacija vremena prijevoza
        self.distributivni_centar.vrijeme_isporuke[porudzbina] = self.env.now
        print(f"Proizvod porudžbine {porudzbina} prevezen na drugu lokaciju")

class DistributivniCentar:
    def __init__(self, env, broj_radnika, kapacitet_skladista, broj_vozila, proizvodi):
        self.env = env
        self.radnici = simpy.Resource(env, capacity=broj_radnika)
        self.skladiste = {proizvod.ime: simpy.Container(env, init=0, capacity=kapacitet_skladista) for proizvod in proizvodi}
        self.transportna_vozila = [TransportnoVozilo(env, self) for _ in range(broj_vozila)]
        self.proizvodi = proizvodi
        self.vrijeme_prijema = {}
        self.vrijeme_obrade = {}
        self.vrijeme_sortiranja = {}
        self.vrijeme_isporuke = {}
        self.ukupno_vrijeme_obrade = 0
        self.broj_isporuka = 0
        self.ukupno_vrijeme_isporuke = 0
        self.broj_radnika = broj_radnika
        self.ukupno_vrijeme_rada = 0

        self.primljeni_paketi = []
        self.obradjeni_paketi = []
        self.sortirani_paketi = []
        self.isporuceni_paketi = []

        # Postavi nivo zaliha za svaki proizvod
        for proizvod in self.proizvodi:
            self.env.process(self.azuriraj_zalihe(proizvod))

    def azuriraj_zalihe(self, proizvod):
        vrijeme = []
        zalihe = []
        while True:
            yield self.env.timeout(1)  # Provera svake vremenske jedinice
            vrijeme.append(self.env.now)
            zalihe.append(self.skladiste[proizvod.ime].level)
            if self.skladiste[proizvod.ime].level < 5:
                print(f"Niski nivo zaliha za proizvod {proizvod.ime}. Trenutni nivo: {self.skladiste[proizvod.ime].level}")
        plt.plot(vrijeme, zalihe, label=f'Zalihe {proizvod.ime}')

    def azuriraj_fazu(self, proizvod, faza):
        proizvod.azuriraj_fazu(faza)


    def primi_porudzbinu(self, porudzbina):
        proizvod = random.choice(self.proizvodi)
        self.vrijeme_prijema[porudzbina] = self.env.now
        self.azuriraj_fazu(proizvod, "Prijem")

        self.primljeni_paketi.append((porudzbina, proizvod))

        yield self.skladiste[proizvod.ime].put(1)  # Dodavanje proizvoda na skladište
        print(f"Porudžbina {porudzbina} ({proizvod.ime}) primljena i dodata na skladište")

    def obradi_porudzbinu(self):
        if self.primljeni_paketi:
            porudzbina, proizvod = self.primljeni_paketi.pop(0)
            with self.radnici.request() as zahtev:
                yield zahtev
                self.ukupno_vrijeme_rada += proizvod.vrijeme_obrade
                yield self.env.timeout(proizvod.vrijeme_obrade)  # Simulacija vremena obrade

            self.vrijeme_obrade[porudzbina] = self.env.now
            self.ukupno_vrijeme_obrade += proizvod.vrijeme_obrade
            self.azuriraj_fazu(proizvod, "Obrada")
            print(f"Porudžbina {porudzbina} ({proizvod.ime}) je obrađena")
            self.obradjeni_paketi.append((porudzbina, proizvod))
        else:
            print(f"Nema primljenih paketa za obradu.")

    def sortiraj_pakete(self):
        if self.obradjeni_paketi:
            porudzbina, proizvod = self.obradjeni_paketi.pop(0)

            # Simulacija vremena sortiranja
            yield self.env.timeout(random.uniform(2, 5))
            self.vrijeme_sortiranja[porudzbina] = self.env.now
            self.azuriraj_fazu(proizvod, "Sortiran")
            print(f"Paketi porudžbine {porudzbina} ({proizvod.ime}) su sortirani")

            self.sortirani_paketi.append((porudzbina, proizvod))
        else:
            print(f"Nema paketa koji su spremni za sortiranje.")

    def otpremi_porudzbinu(self):
        if self.sortirani_paketi:
            # Uzimanje prvog sortiranog paketa po FIFO principu
            porudzbina, proizvod = self.sortirani_paketi.pop(0)

            vozilo = random.choice(self.transportna_vozila)
            with vozilo.vozilo.request() as zahtev:
                yield zahtev
                yield self.env.process(vozilo.prevezi_proizvod(porudzbina))

                self.vrijeme_isporuke[porudzbina] = self.env.now
                self.azuriraj_fazu(proizvod, "Isporucen")
                self.broj_isporuka += 1
                self.ukupno_vrijeme_isporuke += (self.env.now - self.vrijeme_prijema[porudzbina])
                print(f"Porudžbina {porudzbina} ({proizvod.ime}) isporučena")
        else:
            print(f"Nema paketa za isporuku.")

def pokreni_simulaciju(env, distributivni_centar):
    porudzbina_id = 1
    while True:
        interarrival_time = random.expovariate(2)   # Eksponencijalna distribucija s lambda=2
        yield env.timeout(interarrival_time)
        env.process(distributivni_centar.primi_porudzbinu(porudzbina_id))
        env.process(distributivni_centar.obradi_porudzbinu())
        env.process(distributivni_centar.sortiraj_pakete())
        env.process(distributivni_centar.otpremi_porudzbinu())
        porudzbina_id += 1

class Visualization:
    def __init__(self, distributivni_centar):
        self.distributivni_centar = distributivni_centar

    def prikazi_statistike(self):
        # Prikazuje vremena prijema, obrade, sortiranja i isporuke porudžbina
        plt.figure(figsize=(12, 6))
        plt.plot(list(distributivni_centar.vrijeme_prijema.values()), list(distributivni_centar.vrijeme_prijema.keys()), 'ro', label='Prijem')
        plt.plot(list(distributivni_centar.vrijeme_obrade.values()), list(distributivni_centar.vrijeme_obrade.keys()), 'bo', label='Obrada')
        plt.plot(list(distributivni_centar.vrijeme_sortiranja.values()), list(distributivni_centar.vrijeme_sortiranja.keys()), 'go', label='Sortiranje')
        plt.plot(list(distributivni_centar.vrijeme_isporuke.values()), list(distributivni_centar.vrijeme_isporuke.keys()), 'mo', label='Isporuka')
        plt.title('Vremena događaja porudžbina')
        plt.xlabel('Vrijeme (jedinice)')
        plt.ylabel('Porudžbine')
        plt.legend()
        plt.show()

    def prikazi_tabelu_vremena(self):
        porudzbine = list(self.distributivni_centar.vrijeme_prijema.keys())
        data = {
            'Porudzbina': porudzbine,
            'Prijem': [self.distributivni_centar.vrijeme_prijema[p] for p in porudzbine],
            'Obrada': [self.distributivni_centar.vrijeme_obrade.get(p, None) for p in porudzbine],
            'Sortiranje': [self.distributivni_centar.vrijeme_sortiranja.get(p, None) for p in porudzbine],
            'Isporuka': [self.distributivni_centar.vrijeme_isporuke.get(p, None) for p in porudzbine]
        }

        # Formatiraj podatke koristeći tabulate
        table = tabulate(data, headers='keys', tablefmt='pretty')
        print(table)



# Kreiranje okoline i distributivnog centra sa više vrsta proizvoda
env = simpy.Environment()
proizvod1 = Proizvod("Proizvod A", vrijeme_obrade=3, prioritet=1)
proizvod2 = Proizvod("Proizvod B", vrijeme_obrade=5, prioritet=2)
proizvod3 = Proizvod("Proizvod C", vrijeme_obrade=2, prioritet=3)
proizvodi = [proizvod1, proizvod2, proizvod3]
distributivni_centar = DistributivniCentar(env, broj_radnika=3, kapacitet_skladista=20, broj_vozila=2, proizvodi=proizvodi)
env.process(pokreni_simulaciju(env, distributivni_centar))
env.run(until=60)

vizualizacija = Visualization(distributivni_centar)
vizualizacija.prikazi_statistike()
vizualizacija.prikazi_tabelu_vremena()