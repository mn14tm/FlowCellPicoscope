import time
import matplotlib.pyplot as plt
import numpy as np
from picoscope import ps5000a
import photonics.fluorescence as fl

class Picoscope:
    def __init__(self, *args, **kwargs):
        super(Picoscope, self).__init__()
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self):
        self.ps.open()

        # Set resolution
        bitRes = 16
        self.ps.setResolution(str(bitRes))

        self.ps.setChannel("A", coupling="DC", VRange=2.0, VOffset=-1.8, enabled=True, BWLimited=1)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)

        # Set capture duration, s
        waveformDuration = 120E-3
        obsDuration = 1*waveformDuration

        # Set sampling rate, Hz
        sampleFreq = 1E4
        sampleInterval = 1.0 / sampleFreq

        self.res = self.ps.setSamplingInterval(sampleInterval, obsDuration)

        # Print final capture settings
        print("Resolution =  %d Bit" % bitRes)
        print("Sampling frequency = %.3f MHz" % (1E-6/self.res[0]))
        print("Sampling interval = %.f ns" % (self.res[0] * 1E9))
        print("Taking  samples = %d" % self.res[1])
        print("Maximum samples = %d" % self.res[2])

    def closeScope(self):
        self.ps.close()

    def armMeasure(self):
        self.ps.runBlock()

    def measure(self):
        # print("Waiting for trigger")
        while not self.ps.isReady():
            time.sleep(0.001)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def show_signal(self):
        """ Show the signal with the current picoscope settings """

        # Create a time axis for the plots
        x = np.arange(self.res[1]) * self.res[0]
        x *= 1E3  # Convert to milliseconds

        # Collect data
        self.armMeasure()
        data = self.measure()

        # Do plots
        fig, ax = plt.subplots(figsize=(15, 15))
        # creating a timer object and setting an interval of 3000 milliseconds
        timer = fig.canvas.new_timer(interval=3000)
        timer.add_callback(plt.close)
        ax.plot(x, data, 'k.')
        ax.grid(True, which="major")
        ax.set_ylabel('Intensity (A.U.)')
        ax.set_xlim(0, max(x)*1.1)
        ax.axhline(y=0, color='k')
        ax.set_xlabel("Time (ms)")
        # Bring window to the front (above pycharm)
        fig.canvas.manager.window.activateWindow()
        fig.canvas.manager.window.raise_()
        plt.show()
        # print(np.mean(data), np.std(data))

    def show_decay(self):
        """ Measure a single fitting and show with the fit in a plot. """

        # Create a time axis for the plots
        x = np.arange(self.res[1]) * self.res[0]
        x *= 1E3  # Convert to milliseconds

        # Collect data
        self.armMeasure()
        y = self.measure()

        # Fit a single exp. decay function
        popt, perr, chisq = fl.fit_decay(x, y)

        # Do plots
        fig = fl.plot_decay(x, y, fl.decay_fn, popt, log=True, norm=False)
        # Bring window to the front (above pycharm)
        fig.canvas.manager.window.activateWindow()
        fig.canvas.manager.window.raise_()
        plt.show()


if __name__ == "__main__":
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()
    scope.closeScope()
