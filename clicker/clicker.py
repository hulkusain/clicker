"""Clicker"""


class BaseClick(object):
    def __init__(self, config, v_quantity=1, m_quantity=1):
        self._value = config['value']
        self._price = config['price']
        self._mult = 1
        self._mult_max = 10
        self._value_max = 100
        self._scale = 1.15
        self._value_quantity = v_quantity
        self._mult_quantity = m_quantity
        self._mult_price_scale = 100

    def get_value(self):
        return self._value * self._value_quantity

    def get_mult(self):
        return self._mult * self._mult_quantity

    def get_value_quantity(self):
        return self._value_quantity

    def get_mult_quantity(self):
        return self._mult_quantity

    def click(self):
        return self.get_value() * self.get_mult()

    def get_price(self):
        return self._price

    def upgrade(self, type):
        if type == 'value':
            self._upgrade_value()
        elif type == 'mult':
            self._upgrade_mult()

    def _upgrade_value(self):
        if self._value_quantity < self._value_max:
            self._value_quantity += 1

    def _upgrade_mult(self):
        if self._mult_quantity < self._mult_max:
            self._mult_quantity += 1

    def get_upgrades(self):
        upgrades = {}
        if self._value_quantity < self._value_max:
            upgrades['value'] = self.get_value() + self._value
            upgrades['v-price'] = self._upgrade_value_cost()
        if self._mult_quantity < self._mult_max:
            upgrades['mult'] = self.get_mult() + self._mult
            upgrades['m-price'] = self._upgrade_mult_cost()
        return upgrades

    def get_upgrade_cost(self, name, type):
        if type == 'value':
            return self._upgrade_value_cost()
        elif type == 'mult':
            return self._upgrade_mult_cost()
        else:
            return None

    def _upgrade_value_cost(self):
        return int(self._price * (self._scale ** self._value_quantity))

    def _upgrade_mult_cost(self):
        mult_price = self._price * self._mult_price_scale
        return int(mult_price * (self._scale ** self._mult_quantity))


class SuperClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class RandomClick(BaseClick):
    def __init__(self, config, value, price, random):
        super().__init__(config, value, price)
        self._random = random

    def passive_click(self):
        return self._random.randint(0, self.get_value() * self.get_mult())


class BigClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class PassionClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class HyperClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class GhostClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class TnekClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()


class CaptiosusClick(BaseClick):
    def __init__(self, config, value, price):
        super().__init__(config, value, price)

    def passive_click(self):
        return self.click()
