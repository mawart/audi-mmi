class MmiWheel:
  # public:
    def __init__(self, id):
        self._id = id

    def turn(self, id, amount):
        if (self._id == id):
            self._amount = amount

    def getAmount(self):
        return self._state

    def wasTurned(self):
        return self._state != 0

    def update(self):
        if (self._amount != self._state):
            self._state = self._amount
            self._amount = 0

  # private:
    _state = 0
    _amount = 0
    _id = 0x00
