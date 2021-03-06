from django.contrib.gis.db import models
from newsapps.db.utils import get_site_url_root
import re

class SluggedModel(models.Model):
    """
    Extend this class to get a slug field and slug generated from a model
    field. We call the 'get_slug_text', '__unicode__' or '__str__'
    methods (in that order) on save() to get text to slugify. The slug may
    have numbers appended to make sure the slug is unique.
    """
    slug = models.SlugField(max_length=256)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        self.unique_slug()  
        if self.slug == '': raise ValueError, "Slug may not be blank [%s]" % str(self)
        super(SluggedModel,self).save(*args, **kwargs)

    def unique_slug(self):
        """
        Customized unique_slug function
        """
        if not getattr(self, "slug"): # if it's already got a slug, do nothing.
            from django.template.defaultfilters import slugify
            if hasattr(self,'get_slug_text') and callable(self.get_slug_text):
                slug_txt = self.get_slug_text()
            elif hasattr(self,'__unicode__'):
                slug_txt = unicode(self)
            elif hasattr(self,'__str__'):
                slug_txt = str(self)
            else:
                return
            slug = slugify(slug_txt)

            itemModel = self.__class__
            # the following gets all existing slug values
            allSlugs = set(sl.values()[0] for sl in itemModel.objects.values("slug"))
            if slug in allSlugs:
                counterFinder = re.compile(r'-\d+$')
                counter = 2
                slug = "%s-%i" % (slug, counter)
                while slug in allSlugs:
                    slug = re.sub(counterFinder,"-%i" % counter, slug)
                    counter += 1

            setattr(self,"slug",slug)

    def fully_qualified_url(self):        
        return get_site_url_root() + self.get_absolute_url()

class RandomSluggedModel(models.Model):
    """
    Extend this class to get an automatic slug field and autogenerated slug.
    Slug will be a random unique 5 character tinyurl style string.
    *** WARNING: the slug generator assumes everything is case sensitive. Make
    sure your webserver handles urls in a case-sensitive fashion. Some DB
    encoding or collation settings may make queries case-insensitive
    *cough*mysql*cough*. On MySQL, the column might need to be set 
    to UTF8-bin.
    """
    slug = models.SlugField(max_length=5)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        self.unique_slug()  
        if self.slug == '': raise ValueError, "Slug may not be blank [%s]" % str(self)
        super(SluggedModel,self).save(*args, **kwargs)                

    def unique_slug(self):
        """creates random hash key and
        checks it against the db, returns hash key"""
        hashk = self.__generate_url_locator()
        while self.__is_not_unique(hashk):
            hashk = self.__generate_url_locator()

        self.slug=hashk

    def __generate_url_locator(self):
        """This generates a random
        url_locator. it uses a tinyurl style 5 
        character url. This allows for 
        minimal collision probability while 
        allowing for simple recovery """

        number_of_characters = 5
        i = 0
        keys = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        hashk = ""

        while i < number_of_characters:
            random_number = random.randint(0, (len(keys) - 1))
            hashk += keys[random_number]
            i += 1
        return hashk

    def __is_not_unique(self,hashk):
        """Help Function for generate_locator.
        checks the database against keys to avoid
        a hash collision. """

        try:
            group = self.objects.get(slug = hashk)
            not_unique = True
        except self.DoesNotExist:
            not_unique = False

        return not_unique

    def fully_qualified_url(self):        
        return get_site_url_root() + self.get_absolute_url()
