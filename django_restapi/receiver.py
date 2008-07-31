"""
Data format classes that can be plugged into 
model_resource.ModelResource and determine how submissions
of model data need to look like (e.g. form submission MIME types,
XML, JSON, ...).
"""
from django.core import serializers
import django.core.serializers.base

class InvalidFormData(Exception):
    """
    Raised if form data can not be decoded into key-value
    pairs.
    """

class Receiver(object):
    """
    Base class for all "receiver" data format classes.
    All subclasses need to implement the method
    get_data(self, request, method).
    """
    def get_data(self, request, method):
        raise Exception("Receiver subclass needs to implement get_data!")
    
    def get_post_data(self, request):
        return self.get_data(request, 'POST')
    
    def get_put_data(self, request):
        return self.get_data(request, 'PUT')

class FormReceiver(Receiver):
    """
    Data format class with standard Django behavior: 
    POST and PUT data is in form submission format.
    """
    def get_data(self, request, method):
        return getattr(request, method)

class SerializeReceiver(Receiver):
    """
    Base class for all data formats possible
    within Django's serializer framework.
    """
    def __init__(self, format):
        self.format = format
    
    def get_data(self, request, method):
        try:
            print "raw post data is %s:%s " % (repr(self.format),repr(request.raw_post_data))
            deserialized_objects = []
            deserialized = serializers.deserialize(self.format, request.raw_post_data)
            for dobj in deserialized:
                deserialized_objects.append(dobj)
        except django.core.serializers.base.DeserializationError,e:
            print "e is %s" % repr(e)
            raise InvalidFormData
        if len(deserialized_objects) != 1:
            raise InvalidFormData
        model = deserialized_objects[0].object
        print "deseiralized_objects[0] is %s " % repr(dir(deserialized_objects[0]))
        print "model is %s " % repr(type(model))
        data = {}
        for field in model._meta.fields:
            ##print 'field=', field, field.name
            if hasattr(model, field.name):
                data[field.name] = getattr(model, field.name)
                ##print '  val=', getattr(model, field.name)
            else:
                ##print field.default, field.null
                pass
        # m2m = deserialized_objects[0].m2m_data
        # data.update(m2m)
        print 'data=',data
        return data

class JSONReceiver(SerializeReceiver):
    """
    Data format class for form submission in JSON, 
    e.g. for web browsers.
    """
    def __init__(self):
        self.format = 'json'

class XMLReceiver(SerializeReceiver):
    """
    Data format class for form submission in XML, 
    e.g. for software clients.
    """
    def __init__(self):
        self.format = 'xml'
