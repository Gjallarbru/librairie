# Commande pour importer un fichier CSV du catalogue original.
# Ne devrait pas être nécessaire après la mise en service de
# l'application. Plusieurs fonctions d'extraction étant utilisée
# à plusieurs endroits, elles sont séparée afin de standardiser
# le résultat parout dans l'exécution

import openpyxl
from django.core.management import BaseCommand
from django.utils import timezone
from catalog.models import Author, Section, Subsection, Book, Category, BookInstance


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    # def handle(self, *args, **options):
    def handle(self, **options):
        start_time = timezone.now()
        path = options["file_path"]
        wb_obj = openpyxl.load_workbook(path)

        sheet = wb_obj.active

        # ***************************************************
        # Extraction
        # ***************************************************
        data = {}
        # données textuelles
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            # Fait en sorte qu'on saute le rang de titres et créé les clés
            # Créé une clé dictionnaire pour chaque colonne, les rangs
            # étant créés de facto, chaque ligne ayant une entrée par clé
            # -----> Nécessite l'inventaire maître sinon IndexError
            if i == 0:
                data['sections'] = []
                data['titre'] = []
                data['auteur'] = []
                data['cote'] = []
                data['seq'] = []
                data['comment'] = []
                data['statut'] = []
            # Extraction des données
            else:
                d = 0
                for key in data:
                    # pour le texte
                    try:
                        data[key].append(row[d].strip())
                    # pour les chiffres ou entrées nil
                    except AttributeError:
                        data[key].append(row[d])
                    d += 1

        # La librairie insiste pour ajouter la dernière ligne vide
        # et on détruit cette "ligne" ici.
        for key in data:
            data[key].pop()

        # Séparation des listes pour un peu de clareté
        subject_list = data['sections']
        title_list = data['titre']
        author_list = data['auteur']
        cote_list = data['cote']
        seq_list = data['seq']
        cmnt_list = data['comment']
        status_list = data['statut']

        # Liste de sujet sans les grades
        clean_subject_list = self.decrudSubjects(subject_list)
        # Utilisation de "set" pour éliminer les doublons
        self.makeSections(set(clean_subject_list))
        self.makeCategories(clean_subject_list, cote_list)
        self.makeAuthors(author_list, cote_list)
        self.makeBooks(
                cote_list,
                subject_list,
                clean_subject_list,
                title_list,
                author_list,
                )
        nextSeq = self.numberDeFucker(seq_list)
        self.makeBookInstances(
                title_list,
                author_list,
                seq_list,
                cmnt_list,
                status_list,
                nextSeq,
                )

        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Loading xlsx: {(end_time-start_time).total_seconds()} sec."
            )
        )

    def numberDeFucker(self, number_list):
        nums = number_list.copy()
        # Making a list of nones and their indexes
        removal = []
        adjust = 0
        for i in range(len(nums)):
            if nums[i] is None:
                removal.append(i - adjust)
                adjust += 1
        for r in removal:
            nums.pop(r)
        nums.sort()
        nextnum = int(nums[-1])
        return nextnum + 1

    # Retirer les grades qui ne font pas parti du sujet
    def decrudSubjects(self, subject_list):
        temp_list = []
        replacements = [
                (" - Apprenti", ""),
                (" -Apprenti", ""),
                (" - Compagnon", ""),
                ("Compagnon", ""),
                (" - Maître", ""),
                (" -Maître", ""),
                ("... et religion", "et religion"),
                ("\\ et religion", "\\ - et religion"),
                ("Dictionaires", "Dictionnaires"),
                ("Hist. et Géogr.", "Histoire et Géographie"),
                ]
        for line in subject_list:
            # Vérifier la présence de chaqe élément à remplacer
            for r in replacements:
                try:
                    line = line.replace(r[0], r[1])
                # Sil l'objet est None, indiqué comme NonClassé
                except AttributeError:
                    pass
            temp_list.append(line)
        return temp_list

    # Fonction pour séparer les noms et prénoms des auteurs
    # extrait du cvs. S'attend à un seul string
    def splitAuthors(self, unsplit):
        try:
            author = unsplit.split(', ')
            lname = author[0].strip()
            # En présence d'un nom après
            # la virgule (prénom)
            if len(author) > 1:
                fname = author[1].strip()
            # Sans nom après la virgule
            else:
                fname = None
        except AttributeError:
            fname = None
            lname = "Inconnu"
        return (fname, lname)

    # Fonction séparant la cote de livre. Si l'inventaire n'a pas de cote pour un livre,
    # la fonction ne procura que le code d'auteur pour autant que le nom
    # d'auteur soit fourni. Si aucun nom d'auteur indisponible, le code
    # d'auteur sera nécessairement pour INC pour inconnu.
    def splitCote(self, unsplit, last_name="INC"):
        # Créer un tuple depuis la cote
        try:
            cote = unsplit.split('-')
            ctuple = (cote[0].strip(), cote[1].strip())
        # Pour les livres sans cote, spécialement pour les ajouts de Jean-Marie.
        # La cote pourrait être générée si une section fut déclarée à la création du livre
        except AttributeError:
            cote = last_name[:3].strip().upper()
            ctuple = (None, cote)
        return ctuple

    def makeAuthors(self, author_list, cote_list):
        author_names = {}
        author_objects = []
        # author_list est un QuerySet, qui n'a
        # d'index, donc on garde le compte depuis -1
        # qu'on augmente de 1 à chaque itération
        i = -1
        for names in author_list:
            i += 1
            # Extraction pour les noms
            auth_tup = self.splitAuthors(names)
            # Extraction du code d'auteur dont le retour
            # est un tuple (numéro, code de 3 lettres)
            cote = self.splitCote(cote_list[i], auth_tup[1])
            # Créant un dictionnaire avec un tuple de nom
            # comme clé, il y a un standardisation forcée
            # vers un seul code par auteur
            # Tuple utilisé comme clé
            author_names[(auth_tup[0], auth_tup[1])] = cote[1]
        for author_key in author_names:
            a = Author(
                    first_name=author_key[0],
                    last_name=author_key[1],
                    code=author_names[author_key],
                    )
            author_objects.append(a)
        # Pour les livres sans auteurs
        # author_objects.append(
        #         Author(
        #             first_name=None,
        #             last_name="Inconnu",
        #             code="INC")
        #         )
        Author.objects.bulk_create(author_objects) #, ignore_conflicts=True)

    def splitSections(self, s):
        try:
            sections = s.split(' - ')
            section = sections[0].strip()
            if len(sections) > 1:
                subsection = sections[1].strip()
            else:
                subsection = None
        except AttributeError:
            section = "NON CLASSÉ"
            subsection = None
        return (section, subsection)

    def makeSections(self, subject_list):
        section_names = []
        section_objects = []
        subsection_names = []
        subsection_objects = []
        # Séparation des sections via la fonction
        # splitSections
        for s in subject_list:
            section_tup = self.splitSections(s)
            section_names.append(section_tup[0])
            if section_tup[1] is not None:
                subsection_names.append(section_tup[1])
        # Une dernière tentative d'éliminer les doublons
        section_names = set(section_names)
        subsection_names = set(subsection_names)

        for n in section_names:
            # Jean-Marie n'ayant pas respecté la nomenclature, certaines
            # sous-sections serait traitées comme des section principales. Il
            # faut donc vérifier pour ne pas généré des noms indésirés.
            if n not in subsection_names:
                s = Section(name=n)
                section_objects.append(s)
        # Pour usage éventuel
        # section_objects.append(Section(name="NON CLASSÉ"))
        Section.objects.bulk_create(section_objects)

        for n in subsection_names:
            s = Subsection(name=n)
            subsection_objects.append(s)
        Subsection.objects.bulk_create(subsection_objects)

    # La liste de sujet est celle nettoyée des mentions
    # de grade
    def makeCategories(self, subject_list, cote_list):
        cat_dict = {}
        cat_list = []
        i = 0
        for i in range(len(subject_list)):
            # Première préparation
            s, sb = self.splitSections(subject_list[i])
            num = self.splitCote(cote_list[i])[0]
            # S'il n'y avait aucun texte dans la colonne Sujet
            notext = subject_list[i] is None
            match notext:
                case True:
                    s = "NON CLASSÉ"
                    sb = None
                    num = "9999"
                case False:
                    pass
            # Vérifier que le nom de section n'est pas dans les sous-sections.
            isasubsection = Subsection.objects.filter(name=s).exists()
            match isasubsection:
                case True:
                    i += 1
                    continue
                case False:
                    section = Section.objects.get(name=s)
            # Savoir si sb est en fait None, car un section n'a pas toujours de
            # sous-sections.
            subnone = sb is None
            match subnone:
                case True:
                    subsection = None
                case False:
                    subsection = Subsection.objects.get(name=sb)
            # Si le nombre n'existe pas, on ne s'en occupe pas
            nonumber = num is None
            match nonumber:
                case True:
                    continue
                case False:
                    # Si du text existe, il doit être numérique
                    numeric = num.isnumeric()
                    match numeric:
                        case True:
                            number = int(num)
                        case False:
                            continue
            # Agir selon l'existence de la catégorie
            catexists = (section, subsection) in cat_dict
            match catexists:
                # Si la catégorie existe, ne pas inscrire à nouveau
                case True:
                    continue
                # Si la catégorie n'existe pas, on continue
                case False:
                    numexists = False
                    # On vérifie que le numéro n'est pas déjà utilisé, le cas
                    # échant on l'augmente de 1
                    for key in cat_dict:
                        if number == cat_dict[key]:
                            number += 1
                        else:
                            continue
                    cat_dict[(section, subsection)] = number
                    # Création de list d'objects de type Category
                    cat_list.append(Category(section=section, subsection=subsection, number=number))
            i += 1
        Category.objects.bulk_create(cat_list)

    def makeBooks(
            self,
            cote_list,
            subject_list,
            clean_subject_list,
            title_list,
            author_list,
            ):
        # Création du dictionnaire pour éviter les doublons
        book_dict = {}
        # En raison des doublons on ne peut pas simplement
        # demander l'index d'un titre
        i = -1
        for title in title_list:
            i += 1
            # Trouver les grades, le cas échéant
            try:
                apprenti = "Apprenti" in subject_list[i]
                compagnon = "Compagnon" in subject_list[i]
                maitre = "Maître" in subject_list[i]
            # Si le sujet est None
            except TypeError:
                apprenti = False
                compagnon = False
                maitre = False
            # préparer la catégorie via section/sous-sections, le numéro
            # pouvant ne pas être celui du texte.
            stuple = self.splitSections(clean_subject_list[i])
            # Cas idéal, si les sections et sous-sections sont déclarées
            match stuple:
                case (s, None):
                    # Cas avec seulement une section principale
                    try:
                        section = Section.objects.get(name=stuple[0])
                        category = Category.objects.get(section=section, subsection=None)
                    # Cas où seule la sous-section est inscrite --- JMP
                    except Section.DoesNotExist:
                        subsection = Subsection.objects.get(name=stuple[0])
                        category = Category.objects.get(subsection=subsection)
                # Cas idéal, avec section et sous-section
                case (s, sb):
                    section = Section.objects.get(name=stuple[0])
                    subsection = Subsection.objects.get(name=stuple[1])
                    category = Category.objects.get(section=section, subsection=subsection)
            # préparer l'auteur
            names_tup = self.splitAuthors(author_list[i])
            author = Author.objects.get(
                    first_name=names_tup[0],
                    last_name=names_tup[1],
                    )
            # préparer le titre
            title = title_list[i]
            # création d'un Tuple représentant un livre
            b = Book(
                    title=title,
                    author=author,
                    category=category,
                    apprenti=apprenti,
                    compagnon=compagnon,
                    maitre=maitre,
                    )
            book_dict[(title, author.id)] = b
        # Liste pour bulk create
        book_instances = []
        for key in book_dict:
            book_instances.append(book_dict[key])
        return Book.objects.bulk_create(book_instances)

    # Ici, il faut noter que les livres sont créés en premier
    # dans un dictionnaire, ce qui élimine naturellement
    # les 1er livres portant un SEQ identique. Il faut considérer
    # faire le bulk_create avec les erreurs plutôt que d'éliminer
    # l'inscription de certains livres
    def makeBookInstances(
            self, title_list, author_list,
            seq_list, comment_list, status_list, nextSeq):
        # Pour convertir les codes de statut pour ceux courant
        def convertStatus(status):
            match status:
                # Actif - disponible
                # format statut, don, nouveau
                case "A":
                    return ("d", False, False)
                case "B":
                    return ("p", False, False)
                case "I":
                    return ("i", False, False)
                case "L":
                    return ("i", True, False)
                case "N":
                    return ("i", False, True)
                # Par défaut indisponible
                case _:
                    return ("i", False, False)
        # Les titres pouvant être doubles, i = -1
        i = -1
        books = []
        seqs = []
        for title in title_list:
            i += 1
            # Trouver le livre via titre et auteur
            auth_names = self.splitAuthors(author_list[i])
            author = Author.objects.get(
                    first_name=auth_names[0],
                    last_name=auth_names[1])
            book = Book.objects.get(
                    title=title_list[i],
                    author=author,
                    )
            # préparer les infos de l'exemplaire
            seq = seq_list[i]
            comment = comment_list[i]
            status = convertStatus(status_list[i])
            # Assurance contre les SEQ doubles
            seqnotnone = seq is not None
            seqexists = seq in seqs
            match seqnotnone, seqexists:
                # Les seq est inscrit, mais doublon
                case True, True:
                    seq = nextSeq
                    nextSeq += 1
                # Le seq est inscrit normalement
                case True, False:
                    pass
                # Il n'existe aucun seq
                case False, False:
                    seq = nextSeq
                    nextSeq += 1
            instance = BookInstance(
                    book=book,
                    seq=seq,
                    comment=comment,
                    status=status[0],
                    don=status[1],
                    new=status[2],
                    )
            books.append(instance)
            seqs.append(seq)
        BookInstance.objects.bulk_create(books)
