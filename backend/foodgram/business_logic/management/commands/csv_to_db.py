import csv
import os

from django.core.management import BaseCommand

from business_logic.models import Ingredient
from foodgram.settings import BASE_DIR


class Command(BaseCommand):

    def handle(self, *args, **options):

        with open(os.path.join(
            BASE_DIR, '..', '..', 'data', 'ingredients.csv'
        ), 'r', encoding='utf-8') as csvfile:
            dict_reader = csv.reader(csvfile)
            for row in dict_reader:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1],
                )
                if created:
                    ingredient.save()
