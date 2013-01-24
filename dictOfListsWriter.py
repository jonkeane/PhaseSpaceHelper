import csv

def dictOfListsWriter(dict, filename):
    # open file, establish headers
    f = open(filename, 'wb')
    w = csv.writer(f)
    # write headers
    w.writerow(dict.keys())
        
    
    lengths = []
    for key in dict.keys():
        lengths.append(len(dict[key]))

    if len(set(lengths)) != 1:
        print("Error!")

    n = lengths[0]

    for x in range(0,n):
        rw = []
        for key in dict.keys():
            rw.append(dict[key][x])
        w.writerow(rw)

        
    
wordOutput = {}
wordOutput["word"] = []
wordOutput["selfReportedBad"] = []
wordOutput["timecodeStart"] = []
wordOutput["timecodeEnd"] = []

wordOutput["word"].append("vacuum")
wordOutput["selfReportedBad"].append("good")
wordOutput["timecodeStart"].append(2)
wordOutput["timecodeEnd"].append(1)
wordOutput["word"].append("vacuum")
wordOutput["selfReportedBad"].append("bad")
wordOutput["timecodeStart"].append(4)
wordOutput["timecodeEnd"].append(3)


dictOfListsWriter(wordOutput, "test.csv")
