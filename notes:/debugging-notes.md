# Debugging Notes

## Issues Encountered

- Thonny initially ran code using Local Python instead of MicroPython on the Pico.
- The BME688 was detected only after moving I2C to GP16/GP17.
- The OLED caused timeout errors until the correct I2C pins and SoftI2C setup were used.
- LED issues were caused by incomplete ground connections.
- Button input used the Pico internal pull-up resistor.

## Lessons Learned

- I2C devices can scan correctly but still fail if wiring is unstable.
- Breadboard rows and ground rails must be checked carefully.
- State-machine design made the project easier to debug and explain.