import pandas as pd
import numpy as np

def generateCNVMatrix(file_type, input_matrix):
    
    super_class = ['het', 'LOH', "homdel"]
    het_sub_class = ['amp+', 'amp', 'gain', 'neut']
    loh_subclass = ['amp+', 'amp', 'gain', 'neut', "del"]
    hom_del_class = ['0-100kb', '100kb-1Mb', '>1Mb']
    x_labels = ['>40Mb', '10Mb-40Mb', '1Mb-10Mb', '100kb-1Mb', '0-100kb']
  
    df = pd.read_csv(input_matrix, sep='\t')
    
    #make sample by feature matrix for nmf with rows as features and samples as columns
    features = []
    with open('CNV_features.tsv') as f:
        for line in f:
            features.append(line.strip())
    assert(len(features) == 48)                
    columns = df[df.columns[0]].unique()
    nmf_matrix = pd.DataFrame(index=features, columns=columns)
    
    # 2 - total copy number {del=0-1; neut=2; gain=3-4; amp=5-8; amp+=9+}.
    CN_classes = ["del","neut","dup","amp","amp+"] # different total CN states
    CN_class = []
    if file_type == 'ASCAT_NGS':
        for tcn in df['Tumour TCN']:
            if tcn == 2:
                CN_class.append("neut")
            elif tcn == 0 or tcn == 1:
                CN_class.append("del")
            elif tcn == 3 or tcn == 4:
                CN_class.append("gain")
            elif tcn >= 5 and tcn <= 8:
                CN_class.append("amp")
            else:
                CN_class.append("amp+")
        
    elif file_type == 'SEQUENZA':
        for tcn in df['CNt']:
            if tcn == 2:
                CN_class.append("neut")
            elif tcn == 0 or tcn == 1:
                CN_class.append("del")
            elif tcn == 3 or tcn == 4:
                CN_class.append("gain")
            elif tcn >= 5 and tcn <= 8:
                CN_class.append("amp")
            else:
                CN_class.append("amp+")
    elif file_type == "ASCAT":
        for acn, bcn in zip(df['nMajor'], df['nMinor']):
            tcn = acn + bcn
            if tcn == 2:
                CN_class.append("neut")
            elif tcn == 0 or tcn == 1:
                CN_class.append("del")
            elif tcn == 3 or tcn == 4:
                CN_class.append("gain")
            elif tcn >= 5 and tcn <= 8:
                CN_class.append("amp")
            else:
                CN_class.append("amp+")
    elif file_type == 'ABSOLUTE':
        for acn, bcn in zip(df['Modal_HSCN_1'], df['Modal_HSCN_2']):
            tcn = acn + bcn
            if tcn == 2:
                CN_class.append("neut")
            elif tcn == 0 or tcn == 1:
                CN_class.append("del")
            elif tcn == 3 or tcn == 4:
                CN_class.append("gain")
            elif tcn >= 5 and tcn <= 8:
                CN_class.append("amp")
            else:
                CN_class.append("amp+")

    else:
        pass

    df['CN_class'] = CN_class

    
    # 1 - LOH status {hom del; heterozygous; LOH}.
    LOH_status = []

    if file_type == 'ASCAT':               
       for acn, bcn in zip(df['nMajor'], df['nMinor']):
            t = acn + bcn
            if t == 0:
                LOH_status.append("homdel")
            elif acn == 0 or bcn == 0:
                LOH_status.append("LOH")
            else:
                LOH_status.append("het")

    elif file_type == 'SEQUENZA':
        for t, a, b in zip(df['CNt'], df['A'], df['B']):
            if t == 0:
                LOH_status.append("homdel") 
            elif a == 0 or b == 0:
                LOH_status.append("LOH")
            else:
                LOH_status.append("het")
    elif file_type == 'ASCAT_NGS':
        normal_ACN = np.asarray(df['Normal TCN']) - np.asarray(df['Normal BCN'])
        tumour_ACN = np.asarray(df['Tumour TCN']) - np.asarray(df['Tumour BCN'])
        df["Normal ACN"] = list(normal_ACN)
        df["Tumour ACN"] = list(tumour_ACN)

        A_CN = np.asarray(df['Tumour ACN']) #copy number of A allele in tumor
        B_CN = np.asarray(df['Tumour BCN']) #copy number of B allele in tumor
        loh = np.minimum(A_CN, B_CN) #minimum copy number when considering both A and B alleles
        df['loh'] = list(loh)
        for t, a in zip(df['Copy Number'], df['loh']):
            if t == 0:
                LOH_status.append("homdel") 
            elif a == 0:
                LOH_status.append("LOH")
            else:
                LOH_status.append("het")

    elif file_type == 'ABSOLUTE':
        for acn, bcn in zip(df['Modal_HSCN_1'], df['Modal_HSCN_2']):
            t = acn + bcn
            if t == 0:
                LOH_status.append("homdel")
            elif acn == 0 or bcn == 0:
                LOH_status.append("LOH")
            else:
                LOH_status.append("het")
    else:
        print("Please provide a proper file type")

                  
    df['LOH'] = LOH_status
    
    lengths = []
    
    #get chromosomal sizes
    if file_type == 'ASCAT_NGS':
        for start, end in zip(df['Start Position'], df['End Position']):
            lengths.append((end - start)/1000000) #megabases
    elif file_type == 'SEQUENZA':
        for start, end in zip(df['start.pos'], df['end.pos']):
            lengths.append((end - start)/1000000)
    elif file_type == 'ABSOLUTE': #Start End
        for start, end in zip(df['Start'], df['End']):
            lengths.append((end - start)/1000000)
    elif file_type == 'ASCAT':
        for start, end in zip(df['startpos'], df['endpos']):
            lengths.append((end - start)/1000000)
    else:
        pass

    
    df['length'] = lengths
    
    sizes = []
    size_bins = [] #features of matrix(matches Chris's classification)
    hom_del_class = ['0-100kb', '100kb-1Mb', '>1Mb']

    for l, s in zip(lengths, df['LOH']): #keep in mind the lengths are in megabases
        if s == 'homdel':
            if l > -0.01 and l <= 0.1:
                size = "0-100kb"
                size_bin = "(-0.01,0.1]"
            elif l > 0.1 and l <= 1:
                size = "100kb-1Mb"
                size_bin = "(0.1,1]"
            else:
                size = '>1Mb'
                size_bin = "(1,Inf]"
        else:
            if l > -0.01 and l <= 0.1:
                size = "0-100kb"
                size_bin = "(-0.01,0.1]"
            elif l > 0.1 and l <= 1:
                size = "100kb-1Mb"
                size_bin = "(0.1,1]"
            elif l > 1 and l <= 10:
                size = "1Mb-10Mb"
                size_bin = "(1,10]"            
            elif l > 10 and l <= 40:
                size = "10Mb-40Mb"
                size_bin = "(10,40]"
            else:
                size = ">40Mb"
                size_bin = "(40,Inf]"
        sizes.append(size)
        size_bins.append(size_bin)
    df['size_classification'] = sizes
    df['size_bin'] = size_bins
    
    counts = {} #dictionary that maps (sample, feature) to frequency, will be used to populate each cell of matrix    
    for a, c1 in enumerate(super_class):
        df1 = df[df['LOH'] == c1]
        if c1 == 'het':
            for b, c2 in enumerate(het_sub_class): #amp+, amp, etc.
                df2 = df1[df1['CN_class'] == c2]                   
                for j, x in enumerate(x_labels):
                    df3 = df2[df2['size_classification'] == x]
                    for s in df3[df3.columns[0]].unique(): 
                        sample_df = df[df[df.columns[0]] == s]
                        for a, b, c in zip(sample_df['CN_class'], sample_df['LOH'], sample_df['size_classification']):
                            f = a+":"+b+":"+c
                            key = (s, f)
                            value = sample_df.shape[0]
                            if f not in set(features):
                                print (f)
                            else:
                                counts[key] = value
                            
                            
        elif c1 == 'LOH':
            for b, c2 in enumerate(loh_subclass): #amp+, amp, etc.
                df2 = df1[df1['CN_class'] == c2]
                for j, x in enumerate(x_labels):
                    df3 = df2[df2['size_classification'] == x]
                    for s in df3[df3.columns[0]].unique(): 
                        sample_df = df3[df3[df3.columns[0]] == s]
                        for a, b, c in zip(sample_df['CN_class'], sample_df['LOH'], sample_df['size_classification']):
                            f = a+":"+b+":"+c
                            key = (s, f)
                            value = sample_df.shape[0]
                            if f not in set(features):
                                print (f)
                            else:
                                counts[key] = value
                                              
        else: #Hom del
            for b, c3 in enumerate(hom_del_class):
                df3 = df1[df1['size_classification'] == c3]
                for s in df3[df3.columns[0]].unique(): 
                    sample_df = df3[df3[df3.columns[0]] == s]
                    for a, b, c in zip(sample_df['CN_class'], sample_df['LOH'], sample_df['size_classification']):
                        f = "del:homdel:" + c
                        key = (s, f)
                        value = sample_df.shape[0]
                    if f not in set(features):
                        print (f)
                    else:
#                             print (key)
                        counts[key] = value
                          
    #use counts dictionary(which maps (sample, CNV feature) to frequency observed) to populate matrix
    for i, row in enumerate(nmf_matrix.index):
        for j, sample in enumerate(nmf_matrix.columns):
            if (sample, row) in counts:
                nmf_matrix.iat[i, j] = counts[(sample, row)]
            else:
                nmf_matrix.iat[i, j] = 0
                
                
    nmf_matrix.index.name = 'classification'     
    nmf_matrix.to_csv('CNV.' + file_type + '.matrix.tsv', sep='\t')
        
if __name__ == "__main__":
    #generateCNVMatrix("ASCAT", "ASCAT-seg.tsv")
    #generateCNVMatrix("SEQUENZA", "/Users/azhark/Documents/Alexandrov_Lab/CNV/SEQUENZA-seg.tsv")
    #generateCNVMatrix("ABSOLUTE", "forAzhar/CNprograms/ABSOLUTE-seg.txt")
    generateCNVMatrix("ASCAT", "/Users/azhark/Documents/Alexandrov_Lab/CNV/forAzhar/CNprograms/ASCAT-seg.txt")
