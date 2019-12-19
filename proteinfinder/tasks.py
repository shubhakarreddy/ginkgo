from celery import shared_task
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC
from .models import Searches, Status
from .helper import __find_random_protein
from django.db import transaction

@shared_task
@transaction.atomic
def __find_protein(dna_seq, job_id):
    '''
        Given a dna_seq, searches for a protein that it belongs to
        Updates the table entry corresponding to the job_id with the results
        If there is a hit, the status of job is updated to SUCCESS
        If there is no hit, status is updated to NO_MATCH
    '''

    search_db_entry = Searches.objects.filter(id=job_id)
    search_db_entry.update(status=Status.STARTED)

    result = __find_random_protein(dna_seq)
    if result != None:
        search_db_entry.update(status=Status.SUCCESS, sample_id=result["sample_id"],
         protein_id=result["protein_id"], protein_pos=result["protein_pos"])
        return result

    search_db_entry.update(status=Status.NO_MATCH)
    return None
