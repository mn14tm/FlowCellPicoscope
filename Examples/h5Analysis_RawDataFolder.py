from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis

if __name__ == "__main__":

    # Folder to analyse
    timestamp = 1474544405.61158

    print("Analysing...")
    df = folder_analysis(timestamp)

    print("Done! Now plotting...")
    plot_analysis(df, folder=timestamp)
    print("Finito!")
