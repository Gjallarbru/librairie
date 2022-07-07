from django.urls import path
from . import views

# ListView et DetailView sont des classes dans catalog/views.py
urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    # int (integer) : pk (primary key)
    # Ici le paramètre doit porter le nom "pk" vu l'usage d'un générique,
    # mais pourrait porter tout autre nom choise, ou même aucun nom
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    # Liens pour les auteurs
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'),
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    path('borrowedbooks/', views.LoanedBooksListView.as_view(), name='borrowed-books'),
    path('book/<uuid:pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
    path('book/<uuid:pk>/loan/', views.loan_book_librarian, name='loan-book-librarian'),
]
