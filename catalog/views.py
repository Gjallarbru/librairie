import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Book, Author, BookInstance, Section, Subsection  # , Genre
from .forms import RenewBookForm, LoanBookForm


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(
            status__exact='d').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__'   # potential security issue if more fields added)


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


#  @login_required
class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author
    paginate_by = 29


#  @login_required
class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        # Call sur l'implémentation de base
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        # Ajout des données des livres
        context['books'] = Book.objects.filter(author=self.object)
        return context


#  @login_required
class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book


#  @login_required
class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 30

# AJAX
def load_cities(request):
    section_id = request.GET.get('section_id')
    subsections = Subsection.objects.filter(seciton_id=section_id).all()
    return render(request, 'persons/city_dropdown_list_options.html', {'subsection': subsections})

    # return JsonResponse(list(cities.values('id', 'name')), safe=False)
# def search_product(request):
#     """ search function  """
#     if request.method == "POST":
#         query_name = request.POST.get('name', None)
#         if query_name:
#             results = Book.objects.filter(name__contains=query_name)
#             return render(request, 'book-search.html', {"results":results})

#     return render(request, 'book-search.html')


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 30

    def get_queryset(self):
        borrowedbooks = BookInstance.objects\
            .filter(borrower=self.request.user)\
            .filter(status__exact='p')\
            .order_by('due_back')
        print(borrowedbooks)
        return borrowedbooks


class LoanedBooksListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed.html'
    paginate_by = 30

    def get_queryset(self):
        return BookInstance.objects\
                .filter(status__exact='p').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate
        # it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as
            # required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('borrowed-books'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today()\
                + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def loan_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate
        # it with data from the request (binding):
        form = LoanBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as
            # required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['loan_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('borrowed-books'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today()\
                + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_loan_librarian.html', context)
