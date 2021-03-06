#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Usage : 


import pandas as pd
from collections import Counter
from itertools import product
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy as sp
from sklearn.decomposition import PCA





def open_and_test_C_context(path_, input_type, samples_names, cytosine_context):
	#simple function to open and test the Input table file (BSSnper output), it will be called when the object is instanciated
	#open the BS-SNper files as Pandas DataFrames
	#a list of at least 1 path should be provided as input
	#it outputs a list of object of the same length as the input

	checked_list= []

	for sample in path_:
		if input_type == "bssnper":
			sample_input = pd.read_csv(sample, sep = "\t")
			sample_numeric = sample_input.convert_objects(convert_numeric = True) ## the values in the the BS-SNPer output files are read as strings, convert-Objects method allows numeric convertion
																				## "." contained in the BSSnper file are now indicated as NaN
			#check wether the context provided matches with the context found in the BSSnper file
			detected_context = sample_numeric.loc[1, "CONTEXT"]

			assert str(detected_context) == cytosine_context, "Cytosine Context as class attribute ({}) and detected in the input file ({}) don't match".format(cytosine_context, detected_context)


		elif input_type == "bismarkcov":
			sample_input = pd.read_csv(sample, sep = "\t", header = None, names = ["chr", "start", "end", "perc.meth", "count.meth", "count.unmeth"])
			sample_numeric = sample_input.convert_objects(convert_numeric = True)
			#bismark files don't have a coverage column so make on
			sample_numeric["coverage"] = sample_numeric.loc[:, "count.meth"] + sample_numeric.loc[:, "count.unmeth"]

		else:
			raise ValueError(""" Input type not supported, only supported types are "bssnper" and "bismarkcov" """)
		checked_list.append(sample_numeric)

		checked_list_and_names = list(zip(checked_list, samples_names))

	return checked_list_and_names #outputs a list [(pandas dataframe object, name of the object), ...]





def make_path(output_file_path, sample_name, file_extension, compression, supplemental_info):
	#this function make sure the file path is in the correct format: /path/to/file/ and draws the path to save the output file
		
	if output_file_path[-1] == "/":
		output_file_path
	else:
		output_file_path += "/" #adds a slash at the end of the path in case it is missing


	#define compression paramters and file extension
	compression_choice = [("gzip", ".gz"), ("zip", ".zip"), ("bz2", ".bz2"), ("xz", ".xz")]

	if compression:
		for type_comp, extension in compression_choice:
			if type_comp == compression:
				file_name_and_path = "{}{}_{}.{}{}".format(output_file_path, sample_name, supplemental_info, file_extension, extension) #will be used to feed the to_csv() with a string /path/to/filename.extension
				break

			else:
				continue

			raise ValueError("""unrecognized compression type, only valid types are: "gzip", "zip", "bz2", "xz" """)


	else:
		file_name_and_path = "{}{}_{}.{}".format(output_file_path, sample_name, supplemental_info, file_extension)

	return file_name_and_path





def save_BScope_converted_dataframes(BS_conversion_output, output_file_path, object_name, output_type, context, coverage, compression, line_terminator, header=True,  report = True):

		#method to save the DSS or methylkit compatible dataframes generated by the BS_conversion() method as tsv file

		#STEP sort by chromosome and position
		BS_conversion_output.sort_index(axis = 0, level = [0, 1], sort_remaining = True) ## level = [0, 1] combined with sort_remaining = True allows to sort according multi-index level 0(here chr) and then level 1 (here position)

		#use the make_path function to create a file name and a path where to save the output
		path_ = make_path(output_file_path = output_file_path, sample_name = object_name, file_extension = "tsv", compression = "gzip", supplemental_info = "{}_(minCov{})_{}_format_BScope_BS_conversion_output".format(context, coverage, output_type))
				
		print("The output is saved at", path_)

		#save BS_conversion_output
		BS_conversion_output.to_csv(path_or_buf = path_, sep = "\t", header = header, compression = compression, line_terminator  = line_terminator,  encoding = "utf-8")





def BS_report(input_, input_type, output_file_path, output_file_name, context):

		counter = 0

		for df, name in input_:
			if input_type == "DSS":
				df["meth_freq" + name] = (df.loc[:, "X"] / df.loc[:, "N"])*100

			elif input_type == "methylkit":
				df["meth_freq" + name] = df.iloc[:, -2]

			counter += 1
		
		#store the input methylation informatin and the names of the samples in a list
		pandas_dataframe_methylation_list = [df.iloc[:, -1] for df, name in input_] #df.iloc[:, -1] is the last column of each dataframe, the one that contains methylation information
		#a list containing the sample names
		sample_names_list = [name for df, name in input_]
		
		#concatenate all the freq meth columns (and only these ones) in one table and filter out NaN
		methylation_table = pd.concat(pandas_dataframe_methylation_list, axis = 1)

		methylation_table.dropna(axis = 0, how = "any", inplace = True)
		
		#list of arrays containing the concatenated methylation information only
		methylation_list = [methylation_table.iloc[:, i] for i in range(0, methylation_table.shape[1])]
		
		
		##############################################
		#start the plotting function
		##first make a matplotlib figure
		figure = plt.figure(figsize=(30, 30))

		##############################################
		#CpG count in each sample and in the concatenated table
		ax = plt.subplot(3, 2, 1)
		CpG_count_list = [sample.shape[0] for sample, name in input_]  # a list containing the CpG count for each table
		CpG_count_list.append(methylation_table.shape[0]) # add the CpG count for the concateated table
		y = CpG_count_list
		x_pos = [r for r in range(1, len(CpG_count_list)+1)]

		color_list = ["#0077b3"]*len(sample_names_list) #creates a list of color of the same size as the number of samples

		ax.bar(x = x_pos, height = y, color = color_list+["#cccccc"], tick_label = sample_names_list + ["covered in all samples\n(used in subsequent plots)"])
		ax.set_ylabel("{}p{} count".format(context[0], context[1]))
		

		##############################################
		#plot cytosine count on chromosome(eventually will be expressed as fractionof all cytosines))
		ax = plt.subplot(3, 2, 2)
		# groups the rows by chr values and returns the groups attribute of the grouby object
		# the groups attribute is a dictionnary {"group name, here: "chr": (second level of the index, here "pos"}
		
		index_list = methylation_table.index.values
		clist = [c.replace("chr", "") for c, p in index_list]

		chr_num_list=[]
		chr_letter_list=[]
		
		for c in clist: #chromosomes info are treated as strings so far
			
			try:
				b = int(c) #only numbers (here strings that can be converted to integers) are selected other will raise a ValueErros that can be handled by the except statement
				if len(c) <=2: #removes non assembled pieces of chromosomes
					chr_num_list.append(b)

			except ValueError:
				if c == "M" or c == "X" or c == "Y":
					chr_letter_list.append(c)


		chr_num_list.sort() #will sort strings ranking str(int) first
		chr_letter_list.sort()

		chr_list = chr_num_list + chr_letter_list

		values_dict = Counter(chr_list)

		height = list(values_dict.values()) #returns a list of keys
		xlabels =  list(values_dict.keys()) # returns a list of values

		x = list(range(1, len(xlabels) + 1))
	
		ax.bar(x = x, height = height, tick_label = xlabels)
		ax.set_ylabel("{}p{} count".format(context[0], context[1]))
		ax.set_xlabel("Chromosomes")
		ax.set_title("Cytosines count per chromosome")

		##############################################
		#number of cytosines methylated (expressed as percent of cytosines with more than 0% methylation)

		ax = plt.subplot(3, 3, 4)

		methylated_cytosines = []
		totalCytosine = methylation_table.shape[0]

		#filter columns with more than than 0% methylation
		for col_index in range(0, methylation_table.shape[1]):

			meth_filt =  methylation_table.iloc[:, col_index] > 1
			methylated_cytosines_df = methylation_table[meth_filt]
			methylated_cytosines.append(methylated_cytosines_df.shape[0])


		height = [methylated_cytosines/totalCytosine*100 for methylated_cytosines in methylated_cytosines]

		x = list(range(1, len(sample_names_list) + 1))

		ax.bar(x = x, height = height, tick_label = sample_names_list)
		ax.set_ylabel("Percent of total {}p{} bearing methylation".format(context[0], context[1]))
		ax.set_ylim(0, 100)


		##############################################
		#percent methylation at cytosines 
		ax = plt.subplot(3, 3, 5)
		ax.hist(x = methylation_list, bins =50, label = sample_names_list)
		ax.set_ylabel("{}p{} count".format(context[0], context[1]))
		ax.set_xlabel("percent methylation")
		ax.set_xlim(0, 100)
		ax.legend(loc = "upper left")


		##############################################
		#plot mean methylation average for each sample
		ax = plt.subplot(3, 3, 6)
		ax.boxplot(x = methylation_list, notch = True, labels = sample_names_list)
		ax.set_ylabel("sample {}p{} methylation".format(context[0], context[1]))
		ax.set_ylim(0, 105)


		##############################################
		#plot pearson correlation
		ax = plt.subplot(3, 3, 7)
		index = range(0, methylation_table.shape[1])
		index_pairs = list(product(index, repeat = 2))

		pearsons = [sp.stats.pearsonr(methylation_table.iloc[:, a], methylation_table.iloc[:, b]) for a, b in index_pairs]
		pearson_coeffs =[coeff for coeff, pvalue in pearsons]
	
		array1 = np.array(pearson_coeffs)
		array2  = np.array_split(array1, methylation_table.shape[1])
		array3  = np.vstack(array2)

		sns.heatmap(array3, ax = ax, square = True, annot = True, cmap = "GnBu", vmin = 0, vmax = 1, xticklabels = sample_names_list, yticklabels = sample_names_list)
		ax.set_title("Pearson correlation\non methylation values")

		##############################################
		#plot PCA analysis explained variance (scree) and PC1 and PC2
		transposed_table = methylation_table.transpose()
		pca = PCA(n_components = methylation_table.shape[1])
		pc = pca.fit_transform(transposed_table)
		PCA_list = ["PC"+str(n) for n in range(1, methylation_table.shape[1]+1)]

		##PCA scree plot
		ax = plt.subplot(3, 3, 8)
		variance_explained = pca.explained_variance_ratio_
		variance_exp_in_percent = [v*100 for v in variance_explained]
		plt.bar(x = range(1, methylation_table.shape[1]+1), height = variance_exp_in_percent, tick_label = PCA_list)
		plt.ylabel("Percent of variance")
		plt.xlabel("Principal Components (PC)")
		ax.set_title("PCA scree plot on methylation values")

		#PC1, PC2 plot
		ax = plt.subplot(3, 3, 9)
		pc_df = pd.DataFrame(pc, columns = PCA_list, index = sample_names_list)
		ax.scatter(x=pc[:, 0], y=pc[:, 1], edgecolor="face", alpha=0.8, s = 100)
		ax.set_ylabel("Principal Component 1")
		ax.set_xlabel("Principal Component 2")
		ax.set_title("PCA on methylation values")

		#add the marker labels
		for sample in sample_names_list:
			i=sample_names_list.index(sample)
			ax.text(pc[i, 0] - 250, pc[i, 1] + 110, sample, fontsize=8)

		figure.savefig("{}{}_{}_BS_report.png".format(output_file_path, output_file_name, context))






class BsCope:

	def __init__(self, input_file_path, input_type, sample_name, experiment_name, context):

		#the BScope object (Self) contains all these attributes:
		self.path = input_file_path #a list of paths
		self.input_type = input_type # a string "bssnper" or "bismarkcov"
		self.name = sample_name #a list of sample names matching the paths
		self.experiment = experiment_name # a string describing the experiment
		self.context = context
		self.input = open_and_test_C_context(self.path, self.input_type, self.name, self.context) #this attribute stores the actual pandas dataframe file or list of files




	
	def Coverage_plot(self, output_path, coverage_lims = (1, 20)):
		# add a function to visualize the data and decide which parameters to use when calling BS_conversion

		if self.input_type == "bssnper":
			coverage_col1 = "Watson-COVERAGE"
			coverage_col2 = "Crick-COVERAGE"
		
		elif self.input_type == "bismarkcov": 
			coverage_col1 = "coverage"

		else:
			raise ValueError("""Only Input format supported for now are "bssnper" and "bismarkcov" """)
		

		#extract coverage information and plot
		coverage_range = range(coverage_lims[0], coverage_lims[1]+1)
		


		#create a figure and the axes variables that will store as many axes created as needed
		figure, axes = plt.subplots(1, len(self.name), sharey = False, figsize = (20, 5), squeeze = True)

		axes_counter = 0

		for pandas_object, object_name in self.input:
			
			coverage_counts = []
			
			for range_ in coverage_range:
				watson_cov_filter = pandas_object.loc[:, coverage_col1] >= range_
				frame1 = pandas_object[watson_cov_filter]
				number_cytosines = frame1.shape[0]

				if self.input_type == "bssnper":

					crick_cov_filter = pandas_object.loc[:, coverage_col2] >= range_
					frame2 = pandas_object[crick_cov_filter]
					crick_number_cytosines = frame2.shape[0]
					number_cytosines = number_cytosines + crick_number_cytosines

				elif self.input_type == "bismarkcov":

					pass
			

				#generate a list of Cytosines number with coverage >= range_
				coverage_counts.append(number_cytosines)
			

			#generate an axes object and set parameters
			axes[axes_counter].bar(x = coverage_range, height = coverage_counts)
			axes[axes_counter].set_title(object_name)
			axes[axes_counter].set_xlabel("min read coverage cut-off")
			

			axes_counter += 1


		axes[0].set_ylabel("Cytosines count")


		#save the figure as png file
		figure.savefig("{}{}_{}_Coverage_plot.png".format(output_path, self.experiment, self.context))








	def BS_conversion(self, output_type, output_file_path, min_coverage, report = True, header = False, compression = "gzip", line_terminator = "\n"):

		#test the type of output type requested
		assert output_type == "methylkit" or output_type == "DSS", """Unrecognized "output_type" value, only accepted values are "methylkit" or "DSS" """

		#set a few variable to build the dataframes depending on the type of output needed

		if output_type == "methylkit":
			coveragecol_name = "coverage"
			methcol_name = "freq_Meth"
			#col_names will be ["chr", "pos", "strand", "context", "count-Meth(C)", "count-unMeth(T)", "coverage", "freq_Meth", "quality"]


		elif output_type == "DSS":
			coveragecol_name = "N"
			methcol_name = "X"
			header = True #DSS requires a header in its input file
			#col_names will be ["chr", "pos", "N", "X"]


		output_pandas_dataframes_list = []


		if self.input_type == "bssnper":

			for object_, object_name in self.input: #iterate over the different pandas dataframe objects provided as input (self.input attribute) and apply the transformation

				Watson = pd.DataFrame()
				Watson["chr"] = object_.loc[:, "#CHROM"]
				Watson["pos"] = object_.loc[:, "POS"]

				if output_type == "methylkit":
					Watson["strand"] = "+"
					Watson["context"] = object_.loc[:, "CONTEXT"]
					Watson[methcol_name] = object_.loc[:, "Watson-METH"]
					Watson["count-unMeth(T)"] = object_.loc[:, "Watson-COVERAGE"] - object_.loc[:, "Watson-METH"]
					Watson[coveragecol_name] = object_.loc[:, "Watson-COVERAGE"]
					Watson["freq_Meth"] = (object_.loc[:, "Watson-METH"] / object_.loc[:, "Watson-COVERAGE"]) * 100
					Watson["quality"] = object_.loc[:, "Watson-QUAL"]
					
				elif output_type == "DSS":
					Watson[coveragecol_name] = object_.loc[:, "Watson-COVERAGE"]
					Watson[methcol_name] = object_.loc[:, "Watson-METH"]


				# filter for  minimun read coverage
				cov_filter = Watson.loc[:, coveragecol_name] >= min_coverage
				Watson = Watson[cov_filter]


				##Crick
				Crick = pd.DataFrame()
				Crick["chr"] = object_.loc[:, "#CHROM"]
				

				if self.context == "CG":
					Crick["pos"] = object_.loc[:, "POS"] + 1
				elif self.context =="CHG" or self.context =="CHH":
					Crick["pos"] = object_.loc[:, "POS"]
				
				
				if output_type == "methylkit":
					Crick["strand"] = "-"
					Crick["context"] = object_.loc[:, "CONTEXT"]
					Crick[methcol_name] = object_.loc[:, "Crick-METH"]
					Crick["count-unMeth(T)"] = object_.loc[:, "Crick-COVERAGE"] - object_.loc[:, "Crick-METH"]
					Crick[coveragecol_name] = object_.loc[:, "Crick-COVERAGE"]
					Crick["freq_Meth"] = (object_.loc[:, "Crick-METH"] / object_.loc[:, "Crick-COVERAGE"]) * 100
					Crick["quality"] = object_.loc[:, "Crick-QUAL"]
					

				elif output_type == "DSS":
					Crick[coveragecol_name] = object_.loc[:, "Crick-COVERAGE"]
					Crick[methcol_name] = object_.loc[:, "Crick-METH"]


				# filter for  minimun read coverage
				cov_filter = Crick.loc[:, coveragecol_name] >= min_coverage
				Crick = Crick[cov_filter]


				# these lines allow multiindexing of the DataFrame
				Watson.set_index(["chr", "pos"], inplace = True)
				Crick.set_index(["chr", "pos"], inplace = True)


				#STEP2 filter out rows with no methylation information (missing values NaN) by boolean filtering
				Watson.dropna(axis=0, how="any", inplace = True)
				Crick.dropna(axis=0, how="any", inplace = True)


				#STEP3: concatenate the two tables
				final_table = pd.concat([Watson, Crick], axis = 0)


				save_BScope_converted_dataframes(BS_conversion_output = final_table , output_file_path = output_file_path, object_name = object_name, output_type = output_type, context = self.context, coverage = min_coverage, compression = compression, line_terminator  = line_terminator, report = report)
						

				if report:

					output_pandas_dataframes_list.append(final_table)
				
				else:

					pass



		elif self.input_type == "bismarkcov":
		
			if output_type == "methylkit":

				raise ValueError("the bismark.cov files are already compatible with methylkit so I am not doing it!")

			elif output_type == "DSS":

				for object_, object_name in self.input:

					new_DataFrame = pd.DataFrame()
					new_DataFrame["chr"] = object_.loc[:, "chr"]
					new_DataFrame["pos"] = object_.loc[:, "start"]
					new_DataFrame[coveragecol_name] = object_.loc[:, "coverage"]
					new_DataFrame[methcol_name] = object_.loc[:, "count.meth"]


					# filter for  minimun read coverage
					cov_filter = new_DataFrame.loc[:, coveragecol_name] >= min_coverage
					new_DataFrame = new_DataFrame[cov_filter]


					# these lines allow multiindexing of the DataFrame
					new_DataFrame.set_index(["chr", "pos"], inplace = True)
				

					#STEP filter out rows with no methylation information (missing values NaN) by boolean filtering
					new_DataFrame.dropna(axis=0, how="any", inplace = True)

					save_BScope_converted_dataframes(BS_conversion_output = new_DataFrame , output_file_path = output_file_path, object_name = object_name, output_type = output_type, context = self.context, coverage = min_coverage, compression = compression, line_terminator  = line_terminator, report = report)


							
					if report:

						output_pandas_dataframes_list.append(new_DataFrame)
						
					else:

						pass



		if report:

			print("The output {} cytosine files are all done! now preparing the visual report...".format(self.input_type))

			dataframes_and_names = list(zip(output_pandas_dataframes_list, self.name))

			path_ = make_path(output_file_path = output_file_path, sample_name = self.experiment, file_extension="-", compression = compression, supplemental_info = "{}_{}_{}_on_BS_conversion_output".format(self.experiment, self.context, output_type))
			BS_report(dataframes_and_names, input_type = output_type , output_file_path = path_, output_file_name = self.experiment+"_report", context = self.context) # calls the BS_view() function on the BS_conversion output

		else:

			pass
	
