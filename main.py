import random
import sys
import sqlite3

connection = sqlite3.connect('card.s3db')


class MyBank:

    def __init__(self):
        self.card_number = None
        self.card_pin = None
        self.balance = 0

    def create_account(self):
        random.seed()
        while True:
            card_number = self.generate_card_number()
            card_pin = ''.join(str(random.randint(0, 9)) for _ in range(4))
            with connection as con:
                cur = con.cursor()
                if card_number not in [item[0] for item in cur.execute('SELECT number FROM card')]:
                    cur.execute(f'INSERT INTO card '
                                f'(number, pin, balance) '
                                f'VALUES ("{card_number}", "{card_pin}", 0)')
                    con.commit()
                    print(f'\nYour card has been created\nYor card number:\n{card_number}\n'
                          f'Your card PIN:\n{card_pin}\n')
                    break

    @staticmethod
    def checksum(number):
        num = 0
        luhn_multi_by_2 = [int(number[i]) * 2 if i % 2 == 0 else int(number[i]) for i in range(15)]
        luhn_sub_9 = [luhn_multi_by_2[i] - 9 if luhn_multi_by_2[i] > 9 else luhn_multi_by_2[i] for i in range(15)]
        while (sum(luhn_sub_9) + num) % 10:
            num += 1
        return num

    @staticmethod
    def generate_card_number():
        card_num_list = [4, 0, 0, 0, 0, 0] + [random.randint(0, 9) for _ in range(9)]
        card_num = ''.join(map(str, card_num_list))
        return card_num + str(MyBank.checksum(card_num))

    @staticmethod
    def enter_card_number():
        try:
            user_input = int(input('>'))
            if 10 ** 15 < user_input <= 10 ** 16 and str(MyBank.checksum(str(user_input))) == str(user_input)[-1]:
                return str(user_input)
            return None
        except ValueError or TypeError:
            return None

    def log_in(self):
        try:
            print('\nEnter your card number:')
            user_card_no = MyBank.enter_card_number()
            if not user_card_no:
                raise ValueError
            user_pin = input('Enter your PIN:\n>')
            with connection as con:
                cur = con.cursor()
                cur.execute(f'SELECT number, pin, balance FROM card WHERE number = {user_card_no}')
                cards = cur.fetchone()
            if cards is not None and cards[1] == user_pin:
                self.card_number = cards[0]
                self.card_pin = cards[1]
                self.balance = cards[2]
                print('\nYou have successfully logged in!\n')
                return True
            else:
                print('\nWrong card number or PIN!\n')
                return False
        except ValueError:
            print('\nProbably you made a mistake in the card number. Please try again!\n')
            return False

    def log_out(self):
        self.card_number = None
        self.card_pin = None
        self.balance = 0
        print('\nYou have successfully logged out!\n')

    def add_income(self):
        try:
            income = float(input('\nEnter income:\n>'))
            if income < 0:
                raise ValueError
            self.balance += income
            with connection as con:
                cur = con.cursor()
                cur.execute(f'UPDATE card SET balance = {self.balance} WHERE number = {self.card_number}')
                con.commit()
            print('Income was added!\n')
        except ValueError or TypeError:
            print('Incorrect value!!\n')

    def do_transfer(self):
        try:
            print('\nTransfer\nEnter card number:')
            receiver = MyBank.enter_card_number()
            if not receiver:
                raise ValueError
            if receiver == self.card_number:
                raise UserWarning
            with connection as con:
                cur = con.cursor()
                cur.execute(f'SELECT number, balance FROM card WHERE number = {receiver}')
                cards = cur.fetchone()
                if cards is not None:
                    receiver_balance = cards[1]
                    transfer_amount = float(input('Enter how much money you want to transfer:\n>'))
                    if self.balance - transfer_amount >= 0:
                        self.balance -= transfer_amount
                        cur.execute(f'UPDATE card SET balance = {self.balance} WHERE number = {self.card_number}')
                        cur.execute(f'UPDATE card SET balance = {receiver_balance + transfer_amount} \
                                    WHERE number = {receiver}')
                        con.commit()
                        print('Success!\n')
                    else:
                        print('Not enough money!\n')
                else:
                    print('\nSuch a card does not exist.\n')
        except ValueError:
            print('\nProbably you made a mistake in the card number. Please try again!\n')
        except UserWarning:
            print("You can't transfer money to the same account!\n")

    def close_account(self):
        with connection as con:
            cur = con.cursor()
            cur.execute(f'DELETE FROM card WHERE number  = {self.card_number}')
            con.commit()
            print('The account has been closed!')


class Menu:

    def __init__(self):
        self.main_menu = {'1': '. Create an account',
                          '2': '. Log into account',
                          '0': '. Exit'}
        self.account_menu = {'1': '. Balance',
                             '2': '. Add income',
                             '3': '. Do transfer',
                             '4': '. Close account',
                             '5': '. Log out',
                             '0': '. Exit'}
        self.current_menu = self.main_menu

    def show_menu(self):
        for item in self.current_menu.items():
            print(*item, sep='')

    def choose_menu(self, choice):
        if choice == 'main':
            self.current_menu = self.main_menu
        if choice == 'account':
            self.current_menu = self.account_menu


def user_choice(menu):
    user_input = input('>')
    while user_input not in menu.keys():
        print('Wrong choice!')
        user_input = input('>')
    return int(user_input)


def main():
    with connection as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS card "
                    "(id INTEGER PRIMARY KEY, number TEXT, pin TEXT, balance INTEGER DEFAULT 0);")
    menu = Menu()
    bank = MyBank()
    while True:
        if menu.current_menu == menu.main_menu:
            menu.show_menu()
            option = user_choice(menu.current_menu)
            if option == 1:
                bank.create_account()
            elif option == 2:
                if bank.log_in():
                    menu.choose_menu('account')
            elif option == 0:
                conn.close()
                sys.exit()
        elif menu.current_menu == menu.account_menu:
            menu.show_menu()
            option = user_choice(menu.current_menu)
            if option == 1:
                print('\nBalance:', bank.balance, '\n')
            elif option == 2:
                bank.add_income()
            elif option == 3:
                bank.do_transfer()
            elif option == 4:
                bank.close_account()
                menu.choose_menu('main')
            elif option == 5:
                bank.log_out()
                menu.choose_menu('main')
            elif option == 0:
                conn.close()
                sys.exit()


if __name__ == '__main__':
    main()
