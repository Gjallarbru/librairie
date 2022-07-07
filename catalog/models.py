from django.db import models
# Used to generate URLs by reversing the URL patterns
from django.urls import reverse
from django.contrib.auth.models import User
# Required for unique book instances
import uuid
from datetime import date


class Section(models.Model):
    name = models.CharField(
            unique=True,
            max_length=100,
            help_text="Section principale",
            )

    def __str__(self):
        return self.name

    class meta:
        ordering = ['name']


class Subsection(models.Model):
    name = models.CharField(
            unique=True,
            max_length=100,
            help_text="Sous-section",
            )

    def __str__(self):
        return self.name

    class meta:
        ordering = ['name']
        verbose_name = "Sous-section"


class Category(models.Model):
    section = models.ForeignKey(
            Section,
            unique=False,
            related_name='section',
            on_delete=models.CASCADE,
            null=False,
            verbose_name="Section",
            )
    subsection = models.ForeignKey(
            Subsection,
            unique=False,
            related_name='subsection',
            on_delete=models.CASCADE,
            null=True,
            verbose_name="Sous-Section",
            )
    number = models.IntegerField(unique=True)

    def __str__(self):
        number = self.number
        section = self.section.name
        try:
            subsection = self.subsection.name
        except AttributeError:
            subsection = ''
        return "{} / {} / {}".format(
                number,
                section,
                subsection)

    class meta:
        ordering = ['section.name', 'subsection.name']
        verbose_name = "Catégorie"


# Les auteurs
class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(
            "Prénom",
            max_length=100,
            null=True,
            )
    last_name = models.CharField(
            "Nom",
            max_length=100,
            db_index=True,
            )
    code = models.CharField(
            "Code",
            max_length=4)
    date_of_birth = models.DateField(
            "Naissance",
            null=True,
            blank=True)
    date_of_death = models.DateField(
            "Décès",
            null=True,
            blank=True)
    hyper = models.URLField(
            "Hyperlien",
            max_length=200,
            blank=True,
            null=True,
            unique=False)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Auteur'

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name}, {self.first_name}'

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def get_delete_url(self):
        """Returns the url to delete a particular author instance."""
        return reverse('author-delete', args=[str(self.id)])

    def get_update_url(self):
        """Returns the url to update a particular author instance."""
        return reverse('author-update', args=[str(self.id)])


# Représentation d'un livre
class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(
            max_length=200,
            db_index=True,
            )
    # Foreign Key puisque chaque livre peut avoir plus
    # d'un auteur, et chaque auteur plus d'un livre
    author = models.ForeignKey(
            Author,
            related_name='books',
            on_delete=models.SET_NULL,
            null=True,
            verbose_name="Auteur",)
    summary = models.TextField(
            "Sommaire",
            max_length=1000,
            help_text='Une courte description du livre',
            blank=True,
            )
    isbn = models.CharField(
            'ISBN',
            max_length=13,
            #  unique=True,
            help_text='13 Character <a href="https://www.' +
            'isbn-international.org/content/what-isbn"> ' +
            'ISBN number</a>')
    section = models.ForeignKey(
            Section,
            related_name='sec',
            on_delete=models.SET_NULL,
            null=True,
            verbose_name='Section')
    subsection = models.ForeignKey(
            Subsection,
            related_name='subsec',
            on_delete=models.SET_NULL,
            null=True,
            verbose_name='Subsection')
    # category = models.ForeignKey(
    #         Category,
    #         related_name='category',
    #         on_delete=models.SET_NULL,
    #         null=True,
    #         verbose_name='Catégorie')
    apprenti = models.BooleanField(
            null=True,)
    compagnon = models.BooleanField(
            null=True,)
    maitre = models.BooleanField(
            null=True,)

    class Meta:
        ordering = ['title']
        verbose_name = 'Livre'

    def __str__(self):
        """String for representing the Model object."""
        return str(self.title)

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('book-detail', args=[str(self.id)])

    def display_cote(self):
        """String cote dans Admin."""
        cote = "{}-{}".format(self.category.number, self.author.code)
        return cote

    display_cote.short_description = 'Cote'


# Exemplaire physique d'un livre et son statut
class BookInstance(models.Model):
    """Model representing a specific copy of
    a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(
                primary_key=True,
                default=uuid.uuid4,
                help_text='Identifiant unique',)
    book = models.ForeignKey(
                    'Book',
                    on_delete=models.RESTRICT,
                    verbose_name="Livre",
                    null=True)
    seq = models.IntegerField(unique=True,)
    don = models.BooleanField(null=True,)
    new = models.BooleanField(null=True,)
    imprint = models.CharField("Édition", max_length=200)
    due_back = models.DateField("Date de retour", null=True, blank=True)
    borrower = models.ForeignKey(
                User,
                on_delete=models.SET_NULL,
                verbose_name="Emprunteur",
                null=True, blank=True)
    comment = models.CharField(null=True, max_length=200)

    BOOK_STATUS = (
        ('i', 'Inactif'),
        ('p', 'Prêté'),
        ('d', 'Disponible'),
        ('r', 'Reservé'),
        ('a', 'À Vendre'),
        ('v', 'Vendu'),
    )

    status = models.CharField(
        max_length=1,
        choices=BOOK_STATUS,
        blank=True,
        default='d',
        help_text="Disponibilité de l'exemplaire",
    )

    class Meta:
        verbose_name = "Exemplaire"
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set Book as returned"), )

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title}, {self.status})'

    def display_title(self):
        """Create a string for the instance title.
        This is required to display title in Admin."""
        return self.book.title

    display_title.short_description = 'Titre'

    def display_return(self):
        """Create a string for the instance return date."""
        return self.due_back

    display_return.short_description = 'Date de retour'

    def display_status(self):
        """Create a string for the instance status."""
        loan_dict = {
                'm': 'Maintenance',
                'p': 'Prêt',
                'd': 'Disponible',
                'r': 'Reservé',
                'a': 'À Vendre',
                'v': 'Vendu',
            }
        s = self.status
        status = loan_dict[s]
        return status

    display_status.short_description = 'Statut'


class BookComment(models.Model):
    """Model representing a User about a book"""
    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            help_text='Unique ID for this comment')
    book = models.ForeignKey(
            'Book',
            on_delete=models.RESTRICT,
            null=True,
            verbose_name="Livre")
    writer = models.ForeignKey(
                User,
                on_delete=models.SET_NULL,
                verbose_name="Rédacteur",
                null=True)
    text = models.TextField("Commentaire")

    class Meta:
        verbose_name = "Commentaire"
        ordering = ['writer']

    def __str__(self):
        return f'{self.id}, {self.book.title}, {self.text}'

    def display_book(self):
        return self.book.title

    display_book.short_description = 'Titre'

    def display_writer_lname(self):
        return self.writer.last_name

    display_writer_lname.short_description = 'Nom'

    def display_writer_fname(self):
        return self.writer.first_name

    display_writer_fname.short_description = 'Prénom'

