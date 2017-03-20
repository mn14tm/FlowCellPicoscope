from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, copy_data, sweeps_number, text_when_done


if __name__ == "__main__":
    log = {}
    log['measurementID'] = 'T26_decay_vs_pulse'

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    # print("Copying files to network...")
    # copy_data(str(log['measurementID']))
    print("Finito!")
