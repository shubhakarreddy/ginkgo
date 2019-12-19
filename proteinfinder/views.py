from django.shortcuts import render, redirect

from .models import Samples, Proteins, Searches
from .helper import __fetch_and_save_data
from .tasks import __find_protein
import uuid

SEARCH_COOKIE="protein_search_cookie"

# Create your views here.
def index(request):
    '''
        Landing page for the application
        Used to add samples and search for proteins containing DNA
        Messages of tasks are displayed at the top in blue
    '''

    context = {}
    if "message" in request.GET:
        context["message"] = request.GET["message"]
    return render(request, 'query/index.html', context)

def fetch_data(request):
    '''
        Given the NCBI ID, it makes the call to fetch data and save it
        Redirects back to index with a message displayed in the top
    '''

    sample_id = request.POST["sample_id"]
    __fetch_and_save_data(sample_id)

    message = "Fetched sample {} successfully".format(sample_id)
    get_url = "/?" + "message=" + message
    return redirect(get_url)

def show_samples(request):
    '''
        Given a sample_id, it displays the details about the sample
        If no sample_id is given, displays all the samples in db along with
        hyperlinks to see details about them
    '''

    if "sample_id" in request.GET:
        sample_id = request.GET["sample_id"]
        proteins = Proteins.objects.filter(sample__sample_id=sample_id)
        context = {"sample_id": sample_id, "proteins": proteins}
    else:
        samples = Samples.objects.values("sample_id")
        for sample in samples:
            sample["href"] = "/show_samples?sample_id=" + sample["sample_id"]
        context = {"display_all": True, "samples": samples}
    return render(request, 'result/sample_details.html', context)

def find_protein(request):
    '''
        Used to search the protein of the given sequence and returns its
        location
        If a cookie is sent from the client side, it is used to keep track of
        the user that the job belongs to
        If cookie doesn't exist, it is created and cookie is sent to client side
        The search process is called asynchronously and the user is redirected
        to index page to submit further search requests
    '''

    if SEARCH_COOKIE in request.COOKIES:
        cookie_id = request.COOKIES[SEARCH_COOKIE]
    else:
        cookie_id = uuid.uuid4()
    dna_seq = request.POST["dna_seq"]
    search_db_entry = Searches.objects.create(cookie_id=cookie_id, dna_seq=dna_seq)
    job_id = search_db_entry.id

    __find_protein.apply_async(args=[dna_seq, job_id])
    context = {"message": "Job id_{} has been submitted".format(job_id),
                    "cookie_id": cookie_id, "cookie_name": SEARCH_COOKIE}
    return render(request, 'query/index.html', context)

def search_results(request):
    '''
        Used to access the search results based on the cookie_id
        If cookie_id doesn't exist, a message is displayed informing the same
    '''

    if SEARCH_COOKIE in request.COOKIES:
        cookie_id = request.COOKIES[SEARCH_COOKIE]
        search_results = Searches.objects.filter(cookie_id=cookie_id)
        context = {"searches": search_results}
    else:
        context = {"message": "No previous search results available"}

    return render(request, 'result/search_results.html', context)
