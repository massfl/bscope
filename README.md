# bscope

Analysis of genome wide Bisulfite-Sequencing data.


bscope is designed to fulfill two needs encountered during BS-Seq studies:

-First, often various computational tools used in pipeline are incompatible in terms of file structures. bscope transforms two widely used methylation count files bismark.cov and bssnper (post snp removal) files and makes them compatible with two of the most popular used tools to detect differential methylation: DSS and methylkit.

-Second, it is often necessary to visualize the data to get a sense of their overall quality, to that end bscope may output a graphical report on read coverage and methylation levels, see the Coverage_plot() and BS_report() functions respectively.

bscope accepts CpG or CpH methylation files

bscope is a Python3 module and requires Pandas, matplotlib, seaborn, numpy, scipy and sklearn



**USAGE**

**(1) Class BsCope()**

An object of the BsCope class is instantiated:

	object = bscope.BsCope(input_file_path, input_type, sample_name, experiment_name, context)

		.input_file_path
			a list of methylation files and their path, for now bscope accepts only bismark.cov and bssnper output methylation files

		.input_type
			a string indicating the type of files used as input: "bssnper" or "bismarkcov"

		.sample_name
			a list of strings indicating the name of each sample, the sample name should be in the same order as the input_file_path list

		.experiment_name
			a string indicating the name of the experiment

		.context
			a string indicating the genomic context of the cytosines analyzed. It can be "CG" or "CH"


	-->Output: a BsCope python Object with attributes:
		self.path = input_file_path
		self.input_type = input_type
		self.name = sample_name
		self.experiment = experiment_name
		self.context = context
		self.input = a list of pandas DataFrames generated by the open_and_test_C_context() method.



**(2) method Coverage_plot()**

The Coverage_plot() method is applied on the BsCope object to generate a plot of Cytosine counts as a function of read coverage

	object.Coverage_plot(output_path, coverage_lims = (1, 20))
		.output_path
			path of the folder to store the final image into. The name of the image is infered from the self.experiment and 				self.context attributes
		.coverage_lims = (1, 20)
			a range of coverage values to calculate Cytosine count. e.g (1, 20) will count cytosines with coverage up to 20.


**(3) method BS_conversion()**

the BS_conversion() method is applied on the BsCope object to convert the file into the desired output (DSS or methylkit compatible):
	
	object.BS_conversion(output_type,  output_file_path, min_coverage, report = True, header = False, compression = "gzip", 		line_terminator = « \n »)

		.output_type:
			the type of format for the output file: "DSS" or "methylkit".

		.output_file_path:
			the path to the directory where to store the output files (one output file is created for each input file).

		.report:
			whether to call the BS_view() function on the final dataframes and output a graphical report including 					methylation levels, pearson correlation and PCA analysis, default = True
		.min_coverage:
			filter cytosine to keep those with read coverage >= min_coverage
		.header = boolean
			Whether a header line should be added to the final file. False by default unless "DSS" output_type is chosen.
			For DSS type output the following header is used:
			chr 	pos	N	X
			where chr: name of the cromosome
			pos: genomic position in nucleotides
			N: number of reads coverage this position
			X: number of reads indicating methylation

        	.compression:
            		compression of the final output file. Possible values are: None, "gzip", "zip", "bz2", "xz".

        	.line_terminator:
           		 by defaults "/n". can be any character supported by the pandas to_csv() method.https://pandas.pydata.org				/pandas-docs/stable/generated/pandas.DataFrame.to_csv.html

	--> Output: tsv files compatible with DSS or methylkit
	if report = True a visual report, see below BS_view()



**OTHER FUNCTIONS**

**BS_report()**

the BS_report function() generates a visual report containing statistics on the cytosine population
this function is automatically called when report = True in the BS_conversion() method.
**Importantly, this function automatically filters cytosines that are found in all samples before runing ploting functions**

	bscope.BS_report(input_, input_type, output_file_path, output_file_name, context)
		
		input_:
			the output of BS_conversion() method stored in a variable (a list of pandas dataframes)
		input_type: « DSS » or « methylkit »
		output_file_path: path to save the output report image
		output_file_name: name of the output file (infered from self.experiment)
		context: cytosine contex "CG" or "CH" (infered from self.context)

	output:
		a png image with 
		-cytosine counts in eah sample and covered in all samples
		-cytosine count per chromosome
		-plot representing percent of cytosine bearing methylation in each sample
		-count of cytosines per bins of methylation percent
		-mean methylation per sample
		-pearson correlation on methylation levels
		-PCA analysis on mehylation levels (PCA scree plot and PCA plot)


**EXAMPLE:**

In the following example we will:

1-instanciate a BsCope object from two BS-Snper output txt files.

2-Visualize CpG counts as a function of read coverage

3-Run the conversion from BS-SNPer output files to DSS compatible files (A) and generate a visual report (B)

1- bscope_test = BsCope(["/Users/username/bscope_test_file/bssnper_sample1.txt", "/Users/username/bscope_test_file/bssnper_sample2.txt"], "bssnper", ["sample1", "sample2"], "BSCope_test", "CG")

2- bscope_test.Coverage_plot("/Users/username/bscope_test_file/", coverage_lims = (1, 20))

Output:

![bscope_test_cg_coverage_plot](https://user-images.githubusercontent.com/36674021/47658906-38289480-db6a-11e8-9105-badf572c87aa.png)

3- bscope_test.BS_conversion("DSS", "/Users/username/bscope_test_file/", report = True, min_coverage = 10)

Output:

A- DSS compatible files.

sample1

chr | pos | N | X			
--- | --- | - | -			
chr1|3003340|12.0|12.0
chr1|3003582|12.0|10.0
chr1|3003885|14.0|14.0
chr1|3003886|11.0|11.0
chr1|3003898|12.0|11.0
...|...|...|...|			

sample2

chr | pos | N | X
--- | --- | - | -
chr1|3003340|16.0|13.0
chr1|3003582|10.0|10.0
chr1|3003885|14.0|12.0
chr1|3003886|13.0|10.0
chr1|3003898|15.0|11.0
...|...|...|...|

B- Visual Report (.png file)
![bscope_test_bscope_test_cg_dss_on_bs_conversion_output - gzbscope_test_report_cg_bs_report](https://user-images.githubusercontent.com/36674021/47662515-707fa100-db71-11e8-8409-4c0505ef8f9c.png)
