import os
from pyroDB import PickleTable

def pdb_to_csv(pdb_file):
	pdb = PickleTable(pdb_file)
	pdb.to_csv()

if __name__ == '__main__':
	for file in os.scandir('data'):
		if file.name.endswith('.pdb'):
			pdb_to_csv(file.path)