import time
from LabOnChip.HelperFunctions import folder_analysis, plot_analysis

if __name__ == "__main__":

    # Folder to analyse
    timestamp = 1468337701.568398

    print("Analysing...")
    time_start = time.time()
    df = folder_analysis(timestamp)
    time_end = time.time()
    time_elapsed = time_end - time_start
    print("Time taken {:.2f} seconds".format(time_elapsed))

    print("Done! Now plotting...")
    plot_analysis(df, folder=timestamp)
    print("Finito!")
