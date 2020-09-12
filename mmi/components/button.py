from datetime import datetime

def millis():
    dt = datetime.now()
    return dt.microsecond

class Button:
    def __init__(self, input, pushDurationLimit = 300):
      self._input = input
      self._pushDurationLimit = pushDurationLimit

    def isPressed(self):
      return self._buttonState == Button.STATE_PRESSED
    
    def wasPressedFor(self, duration):
      return self._buttonState == Button.STATE_RELEASED and millis() - self._pressTime >= duration
    
    def wasPressedTimes(self, count):
      return self._buttonState == Button.STATE_RELEASED and self._pressCounter == count
    
    def wasPressedTimesOrMore(self, count):
      return self._buttonState == Button.STATE_RELEASED and self._pressCounter >= count
    
    def isHeld(self):
      return self._buttonState == Button.STATE_HELD
    
    def wasHeldFor(self, duration, repeatTime = 0):
      if (self._buttonState != Button.STATE_HELD):
        return False
      
      intervalTime = ((self._updateTime - self._pressTime) - duration + (repeatTime * 0.5)) / repeatTime
      if (intervalTime < 0):
        intervalTime = 0
      
      delayedPressTime = duration + self._pressTime + repeatTime * intervalTime
      return self._updateTime >= delayedPressTime and self._previousUpdateTime < delayedPressTime
    

    def update(self):
      updateTime = millis()
      self._previousUpdateTime = self._updateTime
      self._updateTime = updateTime
      newInputState = self._input.getState()
      
      if (self._inputState != newInputState):
        idleState = Button.STATE_WAITING if updateTime - self._pressTime < self._pushDurationLimit else Button.STATE_RELEASED
        self._buttonState = Button.STATE_PRESSED if newInputState else idleState
        self._inputState = newInputState
        self._stateTime = updateTime
        if (self._buttonState == Button.STATE_PRESSED):
          self._pressTime = updateTime
          self._pressCounter += 1
      
      else:
        if (self._buttonState == Button.STATE_IDLE):
          self._pressCounter = 0
        
        if (self._buttonState == Button.STATE_WAITING):
          self._buttonState = Button.STATE_WAITING if updateTime - self._pressTime < self._pushDurationLimit else Button.STATE_RELEASED
        
        else:
          self._buttonState = Button.STATE_HELD if newInputState else Button.STATE_IDLE  
 
  #private:
    STATE_IDLE     = 0
    STATE_PRESSED  = 1
    STATE_HELD     = 2
    STATE_RELEASED = 3
    STATE_WAITING  = 4
  
    _input = None
    _inputState = False

    _buttonState = STATE_IDLE
    
    _stateTime = 0
    _pressCounter = 0
    _pushDurationLimit = 0
    _pressTime = 0
    _updateTime = 0
    _previousUpdateTime = 0