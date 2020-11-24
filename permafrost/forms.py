# Permafrost Forms
from django.forms import ModelForm
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

from .models import PermafrostRole
class PermafrostRoleCreateForm(ModelForm):
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attrs = self.fields['description'].widget.attrs
        # add Textaread w/o overwriting attrs
        self.fields['description'].widget = Textarea(attrs=attrs)

# class PermafrostRoleEditForm(ModelForm):
#     class Meta:
#         model = PermafrostRole
#         fields = ('name', 'description',)
#         read_only= ('category',)