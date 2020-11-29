class MmiLight:
  # public:
    def __init__(self, lightId, mmi):
        self._mmi = mmi
        self._lightId = lightId

    def on(self):
        self.set(True)

    def off(self):
        self.set(False)

    def toggle(self):
        self.set(not self._state)

    def isOn(self):
        return self._state

    def set(self, state):
        self._state = state
        self._mmi.setLight(self._lightId, state)

  # private:
    _lightId = 0
    _state = False
    _mmi = None


# endif
