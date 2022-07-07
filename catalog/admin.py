from django.contrib import admin
from .models import Author, Book, BookInstance,\
       BookComment, Section, Subsection


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name',
                    'first_name',
                    'code',
                    'hyper',
                    'date_of_birth',
                    'date_of_death')
    fields = ['first_name', 'last_name', 'code', 'hyper', ('date_of_birth', 'date_of_death')]


class BooksInstanceInline(admin.TabularInline):
    model = BookInstance
    # Pour ne pas avoir d'instance vides
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'author',
                    'display_cote')
    inlines = [BooksInstanceInline]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_filter = ('status', 'due_back')
    list_display = ('display_title', 'display_status', 'display_return', 'seq', 'id')
    fieldsets = (
            (None, {
                'fields': ('book', 'imprint', 'seq', 'id')
            }),
            ('Disponibilité', {
                'fields': ('status', 'due_back', 'borrower')
            }),
        )


@admin.register(BookComment)
class BookCommentAdmin(admin.ModelAdmin):
    list_filter = ('book', 'writer')
    list_display = ('display_book', 'display_writer_lname', 'display_writer_fname')


admin.site.register(Section)
admin.site.register(Subsection)
