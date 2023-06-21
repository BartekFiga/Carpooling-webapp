import requests

class RideSharingModel:
    def __init__(self, koszt_km, l_wsp_przejechanych_km, l_pasazerow, stawka_za_dojazd, stawka_za_minute_nadrabiania_trasy,
                 q=3, ob=1, oplata_za_bagaz=2, w1=1, w2=1, O_min=1, O_max=5, Q_min=0, Q_max=10):
        self.koszt_km = koszt_km
        self.l_wsp_przejechanych_km = l_wsp_przejechanych_km
        self.l_pasazerow = l_pasazerow
        self.stawka_za_dojazd = stawka_za_dojazd
        self.stawka_za_minute_nadrabiania_trasy = stawka_za_minute_nadrabiania_trasy
        self.q = q
        self.ob = ob
        self.oplata_za_bagaz = oplata_za_bagaz
        self.w1 = w1
        self.w2 = w2
        self.O_min = O_min
        self.O_max = O_max
        self.Q_min = Q_min
        self.Q_max = Q_max

    def calculate_lm(self, cz_k_p, cz_k):
        return cz_k_p - cz_k

    def calculate_K(self, lm):
        K = self.koszt_km * self.l_wsp_przejechanych_km * self.l_pasazerow + self.stawka_za_dojazd + self.stawka_za_minute_nadrabiania_trasy * (lm + self.q)
        K += self.ob * self.oplata_za_bagaz
        return K

    def calculate_Q(self, K, O):
        return self.w1 * K + self.w2 * O

    def normalize_Q(self, Q):
        return (Q - self.Q_min) / (self.Q_max - self.Q_min)

    def check_constraint_o1(self, a_k, b_k, cz_r, o1):
        return a_k <= o1 <= b_k - cz_r

    def check_constraint_o2(self, c_k, d_k, lm, o2):
        return c_k <= o2 <= d_k + lm + 3

    def check_constraint_o3(self, c_p, d_p, o3):
        return c_p <= o3 <= d_p

    def evaluate(self, cz_k_p, cz_k, cz_r, a_k, b_k, c_k, d_k, c_p, d_p, O1, O2):
        lm = self.calculate_lm(cz_k_p, cz_k)
        K = self.calculate_K(lm)
        O = (O1 + O2) / 2
        Q = self.calculate_Q(K, O)
        Q_norm = self.normalize_Q(Q)

        o1 = b_k - cz_r
        o2 = c_k + lm + 3
        o3 = c_p

        constraint_o1 = self.check_constraint_o1(a_k, b_k, cz_r, o1)
        constraint_o2 = self.check_constraint_o2(c_k, d_k, lm, o2)
        constraint_o3 = self.check_constraint_o3(c_p, d_p, o3)

        if constraint_o1 and constraint_o2 and constraint_o3:
            return {
                'K': K,
                'O': O,
                'Q': Q,
                'Q_norm': Q_norm,
                'constraint_met': True,
            }
        else:
            return {
                'constraint_met': False,
            }

def get_route_info(start_location, end_location, api_key):
    url = f"http://www.mapquestapi.com/directions/v2/route?key={api_key}&from={start_location}&to={end_location}"
    response = requests.get(url)
    data = response.json()

    if data['info']['statuscode'] == 0:
        distance = data['route']['distance']
        time = data['route']['time']
        return distance, time
    else:
        return None, None

def dopasuj_kierowcow(model, lista_kierowcow):
    dopasowani_kierowcy = []

    for kierowca in lista_kierowcow:
        result = model.evaluate(kierowca['cz_k_p'], kierowca['cz_k'], kierowca['cz_r'], kierowca['a_k'],
                                kierowca['b_k'], kierowca['c_k'], kierowca['d_k'], kierowca['c_p'],
                                kierowca['d_p'], kierowca['O1'], kierowca['O2'])

        if result['constraint_met']:
            kierowca['Q_norm'] = result['Q_norm']
            dopasowani_kierowcy.append(kierowca)

    dopasowani_kierowcy.sort(key=lambda x: x['Q_norm'], reverse=True)
    return dopasowani_kierowcy

# Pobranie informacji o trasie
start_location = "Wrocław, Polska"
end_location = "Trzebnica, Polska"
api_key = "BaMRFSo2HQdq4tlertmhjcCjIpXBaGvO"

distance, time = get_route_info(start_location, end_location, api_key)

#if distance is not None and time is not None:
#    print("Długość trasy:", distance, "km")
#    print("Czas trwania trasy:", time, "sekundy")
#else:
#    print("Błąd pobierania informacji o trasie.")


# Użycie klasy RideSharingModel
model = RideSharingModel(koszt_km=1.5, l_wsp_przejechanych_km=distance, l_pasazerow=2, stawka_za_dojazd=5,
                         stawka_za_minute_nadrabiania_trasy=0.5, q=3, ob=1, oplata_za_bagaz=2, w1=1, w2=1)


# Dodatkowi kierowcy
lista_kierowcow = [
    {
        'cz_k_p': time,
        'cz_k': time,
        'cz_r': 10,
        'a_k': 8,
        'b_k': 18,
        'c_k': 20,
        'd_k': 30,
        'c_p': 10,
        'd_p': 20,
        'O1': 4,
        'O2': 3
    },
    {
        'cz_k_p': time,
        'cz_k': time,
        'cz_r': 10,
        'a_k': 8,
        'b_k': 18,
        'c_k': 20,
        'd_k': 20,
        'c_p': 5,
        'd_p': 20,
        'O1': 5,
        'O2': 5
    },
    {
        'cz_k_p': time,
        'cz_k': time,
        'cz_r': 20,
        'a_k': 15,
        'b_k': 25,
        'c_k': 30,
        'd_k': 40,
        'c_p': 20,
        'd_p': 30,
        'O1': 5,
        'O2': 4
    }
]

dopasowani_kierowcy = dopasuj_kierowcow(model, lista_kierowcow)

if len(dopasowani_kierowcy) > 0:
    print("Znaleziono pasujących kierowców:")
    for i, kierowca in enumerate(dopasowani_kierowcy):
        print("Kierowca", i+1)
        print("Q_norm:", kierowca['Q_norm'])
        print()
else:
    print("Brak pasujących kierowców.")