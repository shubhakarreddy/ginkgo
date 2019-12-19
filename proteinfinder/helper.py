from Bio import Entrez
from Bio.Seq import Seq
from Bio import SeqIO
from Bio.Alphabet import IUPAC
from .models import Samples, Proteins, Searches
from datetime import datetime
from django.db import transaction
from suffix_trees import STree
import pickle
import random
import os
import sys
import time
sys.setrecursionlimit(20000)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@transaction.atomic
def __fetch_and_save_data(id, db="nucleotide", retmode="xml"):
    '''
        Fetches data from NCBI website using id and db in retmode format
        Fetches the complete DNA sequence and stores the sequence for each
        protein in the Proteins table of database.
    '''

    handle = Entrez.efetch(db=db, id=id, retmode=retmode)
    record = Entrez.read(handle)
    if Samples.objects.filter(sample_id=id).first() == None:
        sample = Samples.objects.create(sample_id=id, last_used=datetime.now())
    else:
        Samples.objects.filter(sample_id=id).update(last_used=datetime.now())
        sample = Samples.objects.get(sample_id=id)

    proteins = []
    for entry in record[0]["GBSeq_feature-table"]:
        if entry["GBFeature_key"] == "CDS":
            interval = entry["GBFeature_intervals"][0]
            start_pos = int(interval["GBInterval_from"])
            end_pos = int(interval["GBInterval_to"])

            quals = entry["GBFeature_quals"]
            for qual in quals:
                if qual["GBQualifier_name"] == "protein_id":
                    protein_id = qual["GBQualifier_value"]

            proteins.append(Proteins(
                sample=sample,
                protein_id=protein_id,
                start_pos=start_pos,
                end_pos=end_pos
            ))

    handle = Entrez.efetch(db="nuccore", id=id, rettype="gb", retmode="text")
    whole_sequence = SeqIO.read(handle, "genbank")
    whole_sequence = str(whole_sequence.seq)
    for protein in proteins:
        if protein.start_pos < protein.end_pos:
            # normal case where the seq encodes for protein
            protein.protein_seq = whole_sequence[protein.start_pos:protein.end_pos+1]
        else:
            # Case where reverse complement encodes for protein
            dna_seq = Seq(whole_sequence[protein.end_pos-1:protein.start_pos])
            protein.protein_seq = str(dna_seq.reverse_complement())

    Proteins.objects.bulk_create(proteins, ignore_conflicts=True)

    __construct_suffix_trees(id, proteins)

def __construct_suffix_trees(sample_id, proteins):
    '''
        Constructs a file on disk in data folder with name sample_id.pkl
        Iterates through all the proteins and creates a map between protein_ids
        and suffix trees of these sequences
    '''

    tree_map = {}
    for protein in proteins:
        protein_id = str(protein.protein_id)
        protein_seq = str(protein.protein_seq)
        tree_map[protein_id] = STree.STree(protein_seq)

    file_location = os.path.join(BASE_DIR, "data/"+sample_id+".pkl")
    with open(file_location, 'wb') as f:
        pickle.dump(tree_map, f)

    return tree_map

def __find_random_protein(dna_seq):
    '''
        Given a dna sequence, searches for a protein it belongs to by choosing
        proteins at random
        If no protein is found, it returns None
    '''

    random.seed(time.time())
    samples = list(Samples.objects.values("sample_id"))
    while len(samples) > 0:
        random_index = random.randint(0, len(samples)-1)
        sample_id = samples[random_index]["sample_id"]

        file_path = os.path.join(BASE_DIR, "data/"+sample_id+".pkl")
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                tree_map = pickle.load(f)
        else:
            proteins = Proteins.objects.filter(sample__sample_id=sample_id)
            tree_map = __construct_suffix_trees(sample_id, proteins)

        result = __find_location(tree_map, dna_seq)
        if result != None:
            result["sample_id"] = sample_id
            Samples.objects.filter(sample_id=sample_id).update(last_used=datetime.now())
            return result

        del samples[random_index]

    return None

def __find_location(tree_map, dna_seq):
    '''
        Iterates through the tree_map and searches for dna_seq in each suffix
        tree
        Returns the protein_id corresponding to the tree and position in the
        protein if there is a hit
        If not, returns None
    '''

    for protein_id in tree_map:
        pos = tree_map[protein_id].find(dna_seq)
        if pos != -1:
            return {"protein_id": protein_id, "protein_pos": pos}

    return None
