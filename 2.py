class sotrudnik():
    def __init__(self, role1: str, fio1: str):
        self.role = role1
        self.fio = fio1
        self.is_login = False

    def login(self):
        self.is_login = True
        print('Вы авторизовались!')
        return

    def delogin(self):
        self.is_login = False
        print('Вы вышли из системы!')
        return

    def check_if_login(self):
        if self.is_login:
            print('Вы не авторизованы')
        else:
            print('Вы авторизованы')

class kassir(sotrudnik):
    def __init__(self):
        self.id_kassira = 12345
        self.is_check = False
        self.is_give = False

    def check_id(self):
        if self.id_kassira:
            print('Вы успешно вошли в систему')
        else:
            print('Вы не вошли в систему')

    def check_oplata(self):
        if self.is_check:
            print('Вы не проверили оплату!')
        else:
            print('Вы проверили оплату!')

    def check_give(self):
        if self.is_give:
            print('Вы не выдали заказ!')
        else:
            print('Вы выдали заказ!')












