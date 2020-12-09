from collections import OrderedDict

codon_table = {'UUU': 'F', 'CUU': 'L', 'AUU': 'I', 'GUU': 'V', 'UUC': 'F', 'CUC': 'L', 'AUC': 'I', 'GUC': 'V', 'UUA': 'L', 'CUA': 'L', 'AUA': 'I', 'GUA': 'V', 'UUG': 'L', 'CUG': 'L', 'AUG': 'M', 'GUG': 'V', 'UCU': 'S', 'CCU': 'P', 'ACU': 'T', 'GCU': 'A', 'UCC': 'S', 'CCC': 'P', 'ACC': 'T', 'GCC': 'A', 'UCA': 'S', 'CCA': 'P', 'ACA': 'T', 'GCA': 'A', 'UCG': 'S', 'CCG': 'P', 'ACG': 'T', 'GCG': 'A', 'UAU': 'Y', 'CAU': 'H', 'AAU': 'N', 'GAU': 'D', 'UAC': 'Y', 'CAC': 'H', 'AAC': 'N', 'GAC': 'D', 'UAA': 'Stop', 'CAA': 'Q', 'AAA': 'K', 'GAA': 'E', 'UAG': 'Stop', 'CAG': 'Q', 'AAG': 'K', 'GAG': 'E', 'UGU': 'C', 'CGU': 'R', 'AGU': 'S', 'GGU': 'G', 'UGC': 'C', 'CGC': 'R', 'AGC': 'S', 'GGC': 'G', 'UGA': 'Stop', 'CGA': 'R', 'AGA': 'R', 'GGA': 'G', 'UGG': 'W', 'CGG': 'R', 'AGG': 'R', 'GGG': 'G'}
monoisotopic_mass_table = {'A': 71.03711, 'C': 103.00919, 'D': 115.02694, 'E': 129.04259, 'F': 147.06841, 'G': 57.02146, 'H': 137.05891, 'I': 113.08406, 'K': 128.09496, 'L': 113.08406, 'M': 131.04049, 'N': 114.04293, 'P': 97.05276, 'Q': 128.05858, 'R': 156.10111, 'S': 87.03203, 'T': 101.04768, 'V': 99.06841, 'W': 186.07931, 'Y': 163.06333}
monoisotopic_mass_water = 18.01056

def parse_fasta(data_string, first=False):
	dnas = OrderedDict()
	current_dna = None
	for line in data_string.split('\n'):
		if line.startswith('>'):
			current_dna = line[1:].strip()
			dnas[current_dna] = ''
		else:
			dnas[current_dna] += line.strip()
	if first:
		dnas = next(iter(dnas.values()))
	return dnas

def dna_to_rna(dna):
	return dna.replace('T', 'U')

def rna_to_dna(rna):
	return rna.replace('U', 'T')

def rna_to_protein(rna):
	return ''.join(codon_table[rna[n:n + 3]] for n in range(0, len(rna), 3)).strip('Stop')

def reverse_complement(seq, is_rna=True):
	if is_rna:
		return seq.translate(str.maketrans('GUCA', 'CAGU'))[::-1]
	else:
		return seq.translate(str.maketrans('GTCA', 'CAGT'))[::-1]