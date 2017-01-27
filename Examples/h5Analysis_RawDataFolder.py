from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis

if __name__ == "__main__":

    # Folder to analyse
    # timestamp = 1474544405.61158
    timestamp = 'T2_reflectance_standard'

    print("Analysing...")
    df = folder_analysis(folder=timestamp, savename='drop_0p6ms')

    print("Done! Now plotting...")
    plot_analysis(df, folder=timestamp)
    print("Finito!")
