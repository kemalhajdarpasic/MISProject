import simpy
import numpy as np

class DistributivniCentar:
    def __init__(self, env, prosjecan_broj_dolazaka):
        self.env = env
        self.dolazak_vozila = simpy.Store(env) #Store se koristi za čuvanje informacija o dolasku vozila.
        self.prosjecan_broj_dolazaka = prosjecan_broj_dolazaka

    def dolazak_vozila_proces(self):
        vozilo_id = 1
        while True:
            yield self.env.timeout(1)  # Vrijeme između dva dana
            broj_dolazaka = np.random.poisson(self.prosjecan_broj_dolazaka)
            for _ in range(broj_dolazaka):
                broj_paketa = int(np.random.normal(loc=50, scale=10)) # Gausova distribucija, može se koristiti i uniformna, scale je standardna devijacija
                self.dolazak_vozila.put(f"Dan {int(self.env.now)} - Vozilo {vozilo_id}")
                print(f"Dan {int(self.env.now)} - Vozilo {vozilo_id} sa {broj_paketa} paketa stiglo u distributivni centar.")
                vozilo_id += 1

def simuliraj_dolazak_vozila(prosjecan_broj_dolazaka=3, broj_dana=30):
    env = simpy.Environment()
    distributivni_centar = DistributivniCentar(env, prosjecan_broj_dolazaka)

    env.process(distributivni_centar.dolazak_vozila_proces())

    env.run(until=broj_dana)

if __name__ == "__main__":
    simuliraj_dolazak_vozila()
