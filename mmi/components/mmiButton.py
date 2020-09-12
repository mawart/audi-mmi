class MmiButtonInput:
  # public:
    def __init__(self, buttonId):
        self._buttonId = buttonId

    def getState(self):
        return self._state

    def update(self, buttonId, newState):
        if (buttonId == self._buttonId):
            self._state = newState

  # private:
    _buttonId = 0x00
    _state = False


class MmiButton:
  # public:
    def __init__(self, input):
        self._input = input

    def updateTrigger(self, buttonId, newState):
        self._input.update(buttonId, newState)

  # private:
    _input = None
