from restapi.customizer import BaseCustomizer

# from restapi.utilities.logs import log


class Initializer:
    """
    This class is instantiated just after restapi init
    Implement the constructor to add operations performed one-time at initialization
    """

    def __init__(self, services, app=None):
        # c = services['{{auth_service}}']
        pass


class Customizer(BaseCustomizer):
    @staticmethod
    def custom_user_properties_pre(properties):
        extra_properties = {}
        # if 'myfield' in properties:
        #     extra_properties['myfield'] = properties['myfield']
        return properties, extra_properties

    @staticmethod
    def custom_user_properties_post(user, properties, extra_properties, db):
        pass

    @staticmethod
    def manipulate_profile(ref, user, data):
        # data['CustomField'] = user.custom_field

        return data

    @staticmethod
    def get_user_editable_fields(request):

        # return custom fields or a part of them
        # fields = Customizer.get_custom_fields(request)

        # or return something else, maybe an empty dict if extra fields are not editable
        return {}

    @staticmethod
    def get_custom_fields(request):

        # required = request and request.method == "POST"
        """
        return {
            'custom_field': fields.Int(
                required=required,
                # validate=validate.Range(min=0, max=???),
                validate=validate.Range(min=0),
                label="CustomField",
                description="This is a custom field"
            )
        }
        """
        return {}
