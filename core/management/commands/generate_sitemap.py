import glob
import os
import inspect

from django.core.management import BaseCommand
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.template.loader import render_to_string

from kostochka38.sitemap import sitemaps


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('sitemap_folder_path', type=str)

    def handle(self, *args, **options):

        sitemap_folder_path = options['sitemap_folder_path']

        files = glob.glob(os.path.join(sitemap_folder_path, '*'))
        for f in files:
            os.remove(f)

        sitemap_path_list = []
        sitemap_index = 1

        for section in sitemaps:
            if section != 'catalog':
                sitemap = sitemaps[section]
                if inspect.isclass(sitemap):
                    sitemap = sitemap()
                urlset = sitemap.get_urls(protocol='https')
                sitemap_content = render_to_string('sitemap.xml', {'urlset': urlset})
                sitemap_name = 'sitemap%s.xml' % str(sitemap_index)
                sitemap_path = os.path.join(options['sitemap_folder_path'], sitemap_name)
                with open(sitemap_path, 'w') as f:
                    f.write(sitemap_content)
                sitemap_path_list.append('sitemaps/%s' % sitemap_name)
                sitemap_index += 1

        sitemap = sitemaps['catalog']()
        urlset = sitemap.get_urls(protocol='https')
        for i in range(0, len(urlset), 50000):
            chunk = urlset[i:i + 50000]
            sitemap_content = render_to_string('sitemap.xml', {'urlset': chunk})
            sitemap_name = 'sitemap%s.xml' % str(sitemap_index)
            sitemap_path = os.path.join(options['sitemap_folder_path'], sitemap_name)
            with open(sitemap_path, 'w') as f:
                f.write(sitemap_content)
            sitemap_path_list.append('sitemaps/%s' % sitemap_name)
            sitemap_index += 1

        sitemap_content = render_to_string('sitemap_index.xml', {'sitemaps': sitemap_path_list})
        sitemap_path = os.path.join(options['sitemap_folder_path'], 'sitemap.xml')
        with open(sitemap_path, 'w') as f:
            f.write(sitemap_content)