import time

import matplotlib.pyplot as plt
import numpy as np
from picoscope import ps5000a


class Picoscope:
    def __init__(self, *args, **kwargs):
        super(Picoscope, self).__init__()
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self, bitRes=16, obsDuration=120e-3, sampleFreq=1E4):
        self.ps.open()

        # Set bit resolution
        self.ps.setResolution(str(bitRes))

        # Set trigger and channels
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)
        self.ps.setChannel("A", coupling="DC", VRange=10.0, VOffset=-8.0, enabled=True, BWLimited=1)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)

        # Set capture duration (s) and sampling frequency (Hz)
        sampleInterval = 1.0 / sampleFreq
        self.res = self.ps.setSamplingInterval(sampleInterval, obsDuration)

        # Print final capture settings to command line
        print("Resolution =  %d Bit" % bitRes)
        print("Sampling frequency = %.3f MHz" % (1E-6/self.res[0]))
        print("Sampling interval = %.f ns" % (self.res[0] * 1E9))
        print("Taking  samples = %d" % self.res[1])
        print("Maximum samples = %d" % self.res[2])

    def armMeasure(self):
        self.ps.runBlock()

    def measure(self):
        # print("Waiting for trigger")
        while not self.ps.isReady():
            time.sleep(0.001)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def closeScope(self):
        self.ps.close()

    def get_time(self, milli=True):
        """Return time array corresponding to measurement in ms. Set milli=False for time in seconds."""
        x = np.arange(self.res[1]) * self.res[0]
        # Convert to milliseconds
        if milli:
            x *= 1E3
        return x

    def plot(self, show=True, decay=False):
        self.armMeasure()
        y = self.measure()
        x = self.get_time()

        if decay:
            import photonics.photodiode as fl
            # Fit decay
            popt, perr = fl.fit_decay(x, y)
            fig = fl.plot_decay(x, y, fl.decay_fn, popt, log=False, norm=False, show=show)
            return fig
        else:
            # Just plot data
            fig, ax = plt.subplots()
            ax.plot(x, y, '.')
            ax.grid(True, which="major")
            ax.set_ylabel('Intensity (A.U.)')
            ax.set_xlabel("Time (ms)")
            if show:
                plt.show()
            return fig

if __name__ == "__main__":
    scope = Picoscope()
    scope.openScope()
    scope.armMeasure()
    y = scope.measure()
    x = scope.get_time()
    scope.closeScope()

    # Just plot data
    fig, ax = plt.subplots()
    ax.plot(x, y, '.')
    ax.grid(True, which="major")
    ax.set_ylabel('Intensity (A.U.)')
    ax.set_xlabel("Time (ms)")
    plt.show()

    # Fit decay
    import photonics.photodiode as fl

    popt, perr = fl.fit_decay(x, y)
    fig = fl.plot_decay(x, y, fl.decay_fn, popt, log=False, norm=False)
