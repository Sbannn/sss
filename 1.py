class creature():
    def __init__(self, eyes1: int, legs1: int):
        self.eyes = eyes1
        self.legs = legs1
        self.is_alive = True
        self.dist = 0

    def walk(self):
        self.dist += 5*self.legs
        print(f'Ваше существо прошло {self.dist} шагов')
        return

    def die(self):
        self.is_alive = False
        print('Ваше существо умерло')
        return

    def resurrect(self):
        self.is_alive = True
        print('Ваше существо воскресло!')
        return

    def check_if_alive(self):
        if self.is_alive:
            print('Ваше существо живо')
        else:
            print('Ваше существо мертво')

class kotik(creature):
    def __init__(self):
        self.eyes = 2
        self.legs = 4
        self.tail = True
        self.ears = 2
        self.is_washed = False
        self.is_alive = True
        self.dist = 0

    def wash_face(self):
        self.is_washed = True
        print('Ваш котик помылся')
        if self.ears < 2:
            self.ears += 1
            print(f'Текущее количество ушей {self.ears}')

    def walk_cat(self):
        self.walk()
        if self.is_washed:
            self.is_washed = False
            print('Ой, ваш котик испачкался!')
        else:
            if self.ears > 0:
                self.ears -= 1
                print(f'Текущее количество ушей {self.ears}')
            else:
                self.die()

"""
FAP = creature(2, 2)
for i in range(5):
    FAP.walk()
FAP.check_if_alive()
FAP.die()
FAP.check_if_alive()
FAP.resurrect()
FAP.check_if_alive()"""
Andrey = kotik()
Andrey.check_if_alive()
for i in range(5):
    Andrey.walk_cat()
Andrey.wash_face()